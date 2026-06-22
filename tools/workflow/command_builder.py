import os

from configs.path_config import PROJECT_ROOT
from configs.workflow_config import DEFAULT_WORKFLOW_ARGS, SUPPORTED_PIPELINES
from configs.app_config import APP_PASCAL
from tools.workflow.nf.methylong.helper import _resolve_methylong_models
from utils.common_utils import _find_free_gpu
from utils.runner_utils import _find_dorado_lib_path_in_image

try:
    from configs.workflow_config import MAX_WORKFLOW_RESOURCES, NEXTFLOW_OFFLINE
except ImportError:
    MAX_WORKFLOW_RESOURCES = {"max_cpus": None, "max_memory": "30.GB", "max_time": "72.h"}
    NEXTFLOW_OFFLINE = True


def _join_data_dir(base_data_dir: str, p: str) -> str:
    if not p:
        return p
    return os.path.join(base_data_dir, os.path.basename(str(p)))


def _resolve_pipeline_path(pipeline: str) -> str:
    """
    Resolve pipeline to an absolute path or nf-core name.
    1. Already absolute / contains '/' → use as-is
    2. In SUPPORTED_PIPELINES → look up DATA_PATH["workflow"]["pipeline_dir"],
       fall back to PROJECT_ROOT/agent_workflow/<name>
    3. Otherwise → treat as nf-core/<name>
    """
    if "/" in pipeline or os.path.exists(pipeline):
        return pipeline

    if pipeline.lower() in [name.lower() for name in SUPPORTED_PIPELINES]:
        from configs import DATA_PATH
        configured = DATA_PATH.get("workflow", {}).get("pipeline_dir", "")
        if configured:
            base = os.path.abspath(os.path.expanduser(configured))
        else:
            base = os.path.join(PROJECT_ROOT, "agent_workflow")
        return os.path.join(base, pipeline)

    return f"nf-core/{pipeline}"


def _bam_has_mod_tags(bam_path: str) -> bool:
    """Return True if the BAM already has MM/ML modification tags (modBAM)."""
    try:
        import pysam
        with pysam.AlignmentFile(bam_path, "rb", check_sq=False) as bam:
            for i, read in enumerate(bam.fetch(until_eof=True)):
                if read.has_tag("MM") or read.has_tag("Mm"):
                    return True
                if i >= 99:
                    break
        return False
    except Exception as e:
        print(f"[CmdBuilder] MM tag check failed: {e}")
        return False


def _samplesheet_pacbio_needs_modcall(input_file: str) -> bool:
    """Return True if any PacBio sample needs --pacbio_modcall.
    method='pacbio' + no MM/ML tags in BAM → needs modcall.
    Falls back to True if BAM is unreadable.
    """
    if not input_file or not os.path.isfile(input_file):
        return False
    try:
        with open(input_file, encoding="utf-8") as f:
            header_line = f.readline().strip().lower()
            cols = [c.strip() for c in header_line.split(",")]
            if "method" not in cols:
                return False
            method_idx = cols.index("method")
            path_idx   = cols.index("path") if "path" in cols else -1
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [c.strip() for c in line.split(",")]
                if method_idx >= len(parts):
                    continue
                if parts[method_idx].lower() != "pacbio":
                    continue
                bam = parts[path_idx] if 0 <= path_idx < len(parts) else ""
                # If path is a directory, pick the first BAM inside
                if bam and os.path.isdir(bam):
                    bam_files = [e.path for e in os.scandir(bam)
                                 if e.name.lower().endswith(".bam")]
                    bam = bam_files[0] if bam_files else ""
                if bam and os.path.isfile(bam):
                    if _bam_has_mod_tags(bam):
                        print(f"[CmdBuilder] {os.path.basename(bam)}: MM/ML tags present → modBAM, skip modcall")
                        continue
                    print(f"[CmdBuilder] {os.path.basename(bam)}: no MM/ML tags → needs --pacbio_modcall")
                    return True
                else:
                    print(f"[CmdBuilder] method='pacbio', BAM not accessible → needs --pacbio_modcall")
                    return True
        return False
    except Exception as e:
        print(f"[CmdBuilder] _samplesheet_pacbio_needs_modcall error: {e}")
        return False


def _path_has_pod5(p: str) -> bool:
    """Return True if p is a .pod5 file, or a directory containing any .pod5 file."""
    p = p.strip()
    if p.lower().endswith(".pod5") and os.path.isfile(p):
        return True
    if os.path.isdir(p):
        for entry in os.scandir(p):
            if entry.name.lower().endswith(".pod5"):
                return True
    return False


def _samplesheet_needs_dorado(input_file: str) -> bool:
    """Return True if any sample provides raw POD5 input (needs Dorado basecalling)."""
    if not input_file or not os.path.isfile(input_file):
        return False
    try:
        import csv as _csv
        with open(input_file, encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                if _path_has_pod5(row.get("path") or ""):
                    return True
        return False
    except Exception:
        return False


def build_workflow_command(kwargs: dict, data_path: dict) -> str:
    """
    构建 nextflow 工作流命令。
    支持本地工作流和 nf-core 工作流。

    返回格式：export NXF_OFFLINE=true\nnextflow run ...
    """
    base_data_dir = os.path.abspath(os.path.expanduser(data_path.get("base_data_dir", "~/agent_data")))
    out_dir = os.path.abspath(os.path.expanduser(data_path.get("out_dir", base_data_dir)))

    pipeline = kwargs.get("pipeline", "")
    pipeline_path = _resolve_pipeline_path(pipeline)

    profile = DEFAULT_WORKFLOW_ARGS.get("profile", "singularity")

    # input 可能是绝对路径（前置文件）或相对文件名（用户上传文件）
    input_raw = kwargs.get("input", "")
    if os.path.isabs(input_raw):
        input_file = os.path.abspath(input_raw)
    else:
        input_file = os.path.abspath(_join_data_dir(base_data_dir, input_raw))

    outdir_raw = kwargs.get("outdir", "results")
    if os.path.isabs(outdir_raw):
        outdir = os.path.abspath(outdir_raw)
    else:
        outdir = os.path.abspath(_join_data_dir(out_dir, outdir_raw))

    cmd_parts = [
        "nextflow run",
        pipeline_path,
        f"--input {input_file}",
        f"--outdir {outdir}",
        f"-profile {profile}",
    ]
    extra_binds    = []
    dorado_image_path = ""
    # methylong 专用：检测 samplesheet 决定是否注入 dorado 模型 / --pacbio_modcall
    needs_pacbio_modcall = False
    if pipeline.lower() == "methylong":
        needs_dorado         = _samplesheet_needs_dorado(input_file)
        needs_pacbio_modcall = _samplesheet_pacbio_needs_modcall(input_file)
        print(f"[CmdBuilder] needs_dorado={needs_dorado}  needs_pacbio_modcall={needs_pacbio_modcall}")

        from configs import DATA_PATH as _FULL_DATA_PATH
        simplex_model, mod_model = _resolve_methylong_models(_FULL_DATA_PATH)

        if needs_dorado:
            if simplex_model:
                cmd_parts.append(f"--dorado_model {simplex_model}")
                extra_binds.append(os.path.dirname(simplex_model))
                print(f"[CmdBuilder] dorado_model: {simplex_model}")
            else:
                print("[CmdBuilder] WARNING: dorado_model not found in model_dir")
            if mod_model:
                cmd_parts.append(f"--dorado_modification_model {mod_model}")
                print(f"[CmdBuilder] dorado_modification_model: {mod_model}")
            else:
                print("[CmdBuilder] WARNING: dorado_modification_model not found in model_dir")
        else:
            print("[CmdBuilder] PacBio-only samplesheet — skipping dorado model params")

        from configs import IMAGE_PATH as _IMAGE_PATH
        img_dir = os.path.join(
            os.path.expanduser(_IMAGE_PATH['image_store']),
            "workflow", "methylong"
        )
        if os.path.isdir(img_dir):
            for f in os.listdir(img_dir):
                if f.endswith((".img", ".sif")) and "dorado" in f:
                    dorado_image_path = os.path.join(img_dir, f)
                    break

    # LLM 生成的可选参数 — 排除已手动处理的 key，避免重复
    _HANDLED = {"pipeline", "input", "outdir", "config",
                "dorado_model", "dorado_modification_model", "pacbio_modcall"}
    for key, value in kwargs.items():
        if key in _HANDLED:
            continue
        if value is True:
            cmd_parts.append(f"--{key}")
        elif value not in (False, None, ""):
            cmd_parts.append(f"--{key} {value}")

    # --pacbio_modcall 最后追加，覆盖任何 LLM 可能传入的值
    if needs_pacbio_modcall:
        cmd_parts.append("--pacbio_modcall")

    if kwargs.get("config"):
        cmd_parts.append(f"-c {os.path.abspath(kwargs['config'])}")

    # work 目录不显式指定，由 nextflow 在 cd 后的 run_dir 下自动创建 work/

    # 资源上限 —— 写入 override.config，用 -c 注入，可覆盖流水线内写死的值
    max_cpus   = MAX_WORKFLOW_RESOURCES.get("max_cpus") or os.cpu_count() or 8
    max_memory = MAX_WORKFLOW_RESOURCES.get("max_memory", "30.GB")
    max_time   = MAX_WORKFLOW_RESOURCES.get("max_time",   "72.h")

    override_cfg = _write_resource_override_config(outdir, max_cpus, max_memory, max_time, extra_binds=extra_binds, dorado_image_path=dorado_image_path)
    if override_cfg:
        cmd_parts.append(f"-c {override_cfg}")

    # 组合命令：先设置环境变量，再执行 nextflow
    nextflow_cmd = " ".join(cmd_parts)
    env_parts = []
    nfcore_home = data_path.get("nfcore_home", "")
    if nfcore_home:
        env_parts.append(f"export NXF_HOME={os.path.abspath(os.path.expanduser(nfcore_home))}")
    if NEXTFLOW_OFFLINE:
        env_parts.append("export NXF_OFFLINE=true")
    env_parts.append(nextflow_cmd)
    full_cmd = " && ".join(env_parts)

    return full_cmd


def _write_resource_override_config(run_dir: str, max_cpus: int,
                                    max_memory: str, max_time: str,
                                    extra_binds: list[str] = None,
                                    dorado_image_path: str = "") -> str:
    if not run_dir:
        return ""

    os.makedirs(run_dir, exist_ok=True)
    cfg_path = os.path.join(run_dir, "override.config")

    gpu_device = _find_free_gpu(min_free_mb=10000)

    extra_bind_str = ""
    if extra_binds:
        parts = [f"--bind {p}:{p}" for p in extra_binds if p and os.path.exists(p)]
        if parts:
            extra_bind_str = " " + " ".join(parts)

    dorado_lib = _find_dorado_lib_path_in_image(dorado_image_path) if dorado_image_path else ""
    ld_parts = [p for p in [dorado_lib, "/usr/local/nvidia/lib64", "/usr/local/nvidia/lib"] if p]
    ld_library_path = ":".join(ld_parts)

    content = f"""\
// Auto-generated by {APP_PASCAL}
singularity {{
    enabled = true
    runOptions = "--nv --bind /usr/local/nvidia:/usr/local/nvidia{extra_bind_str} --env LD_LIBRARY_PATH={ld_library_path}"
}}

process {{
    resourceLimits = [
        cpus:   {max_cpus},
        memory: '{max_memory}',
        time:   '{max_time}'
    ]
    withName: 'DORADO_BASECALLER' {{
        ext.use_gpu = true
        ext.args = '--device {gpu_device}'
    }}
    withName: 'DORADO_ALIGNER' {{
        beforeScript = 'outdir=$(grep -oP "(?<=--output-dir )\\\\S+" .command.sh 2>/dev/null | head -1); [ -n "$outdir" ] && mkdir -p "$outdir" || true'
        ext.args = {{ "--output-dir ${{meta.id}} && find ${{meta.id}} -mindepth 2 '(' -name '*.bam' -o -name '*.bai' ')' -exec mv {{}} ${{meta.id}}/ ';' 2>/dev/null || true" }}
    }}
}}
"""
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(content)
    return cfg_path
