import os

from configs import IMAGE_PATH
from configs.path_config import PROJECT_ROOT
from configs.workflow_config import DEFAULT_WORKFLOW_ARGS, SUPPORTED_PIPELINES


def _join_data_dir(base_data_dir: str, p: str) -> str:
    if not p:
        return p
    return os.path.join(base_data_dir, os.path.basename(str(p)))


def _resolve_pipeline_path(pipeline: str) -> str:
    """
    解析 pipeline 路径：
    1. 如果是完整路径或包含 / 的路径，直接返回
    2. 如果是支持的本地工作流名（如 methylong），返回 agent_workflow/{name}
    3. 否则默认认为是 nf-core 的 {pipeline}
    """
    if "/" in pipeline or os.path.exists(pipeline):
        return pipeline
    
    # 检查是否是支持的本地工作流
    if pipeline.lower() in [name.lower() for name in SUPPORTED_PIPELINES]:
        # 优先使用本地工作流（agent_workflow 目录下）
        return f"agent_workflow/{pipeline}"
    
    # 默认认为是 nf-core
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

    # 添加可选参数
    if kwargs.get("genome"):
        cmd_parts.append(f"--genome {kwargs['genome']}")
    if kwargs.get("config"):
        cmd_parts.append(f"-c {os.path.abspath(kwargs['config'])}")
    if kwargs.get("extra_args"):
        cmd_parts.append(kwargs["extra_args"])

    # 组合命令：先设置环境变量，再执行 nextflow
    nextflow_cmd = " ".join(cmd_parts)
    full_cmd = f"export NXF_OFFLINE=true\n{nextflow_cmd}"
    
    return full_cmd
