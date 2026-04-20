import os

from configs.path_config import PROJECT_ROOT
from configs.workflow_config import DEFAULT_WORKFLOW_ARGS, SUPPORTED_PIPELINES
from tools.workflow.methylong.helper import _resolve_methylong_models
from utils.common_utils import _find_free_gpu
from utils.runner_utils import _find_dorado_lib_path_in_image

try:
    from configs.workflow_config import MAX_WORKFLOW_RESOURCES
except ImportError:
    MAX_WORKFLOW_RESOURCES = {"max_cpus": None, "max_memory": "30.GB", "max_time": "72.h"}


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


def build_workflow_command(kwargs: dict, data_path: dict) -> str:
    """
    构建 nextflow 工作流命令。
    支持本地工作流和 nf-core 工作流。
    
    返回格式：export NXF_OFFLINE=true\nnextflow run ...
    """
    # 确保路径为绝对路径
    base_data_dir = os.path.abspath(os.path.expanduser(data_path.get("base_data_dir", "~/agent_data")))
    out_dir = os.path.abspath(os.path.expanduser(data_path.get("out_dir", base_data_dir)))

    pipeline = kwargs.get("pipeline", "")
    pipeline_path = _resolve_pipeline_path(pipeline)

    profile = DEFAULT_WORKFLOW_ARGS.get("profile", "singularity")
    
    # input 可能是绝对路径（前置文件）或相对文件名（用户上传文件）
    input_raw = kwargs.get("input", "")
    if os.path.isabs(input_raw):
        # 已是绝对路径，直接用
        input_file = os.path.abspath(input_raw)
    else:
        # 相对路径或文件名，加上 base_data_dir
        input_file = os.path.abspath(_join_data_dir(base_data_dir, input_raw))
    
    outdir_raw = kwargs.get("outdir", "results")
    if os.path.isabs(outdir_raw):
        outdir = os.path.abspath(outdir_raw)
    else:
        outdir = os.path.abspath(_join_data_dir(out_dir, outdir_raw))

    # 构建基础命令（简化版，仅保留必要参数）
    cmd_parts = [
        "nextflow run",
        pipeline_path,
        f"--input {input_file}",
        f"--outdir {outdir}",
        f"-profile {profile}",
    ]
    extra_binds = []
    dorado_image_path = ""
    # methylong：自动注入本地 dorado 模型路径
    if pipeline.lower() == "methylong":
        from configs import DATA_PATH as _FULL_DATA_PATH
        simplex_model, mod_model = _resolve_methylong_models(_FULL_DATA_PATH)
        if simplex_model:
            cmd_parts.append(f"--dorado_model {simplex_model}")
            extra_binds.append(os.path.dirname(simplex_model))  # 模型父目录
            print(f"[CmdBuilder] dorado_model: {simplex_model}")
        else:
            print("[CmdBuilder] WARNING: dorado_model not found in model_dir")

        if mod_model:
            cmd_parts.append(f"--dorado_modification_model {mod_model}")
            # 父目录相同，不重复添加
            print(f"[CmdBuilder] dorado_modification_model: {mod_model}")
        else:
            print("[CmdBuilder] WARNING: dorado_modification_model not found in model_dir")

        from configs import IMAGE_PATH as _IMAGE_PATH
        img_dir = os.path.join(
            os.path.expanduser(_IMAGE_PATH['image_store']),
            "workflow", "methylong"
        )
        # cmd_parts.append('--dorado_aligner_args "--output-dir ."')
        if os.path.isdir(img_dir):
            for f in os.listdir(img_dir):
                if f.endswith((".img", ".sif")) and "dorado" in f:
                    dorado_image_path = os.path.join(img_dir, f)
                    break

    # 添加可选参数
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
    full_cmd = f"export NXF_OFFLINE=true && {nextflow_cmd}"

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
// Auto-generated by BioAgent
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
