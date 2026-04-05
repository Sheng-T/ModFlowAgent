import os

from configs import IMAGE_PATH
from configs.workflow_config import DEFAULT_WORKFLOW_ARGS


def _join_data_dir(base_data_dir: str, p: str) -> str:
    if not p:
        return p
    return os.path.join(base_data_dir, os.path.basename(str(p)))


def build_workflow_command(kwargs: dict, data_path: dict) -> str:
    # 确保路径为绝对路径，这对容器挂载至关重要
    base_data_dir = os.path.abspath(os.path.expanduser(data_path.get("base_data_dir", "~/agent_data")))
    work_dir = os.path.abspath(os.path.expanduser(data_path.get("work_dir", "~/agent_data/nextflow_work")))

    pipeline = kwargs.get("pipeline", "")
    # 如果不是路径，默认认为是 nf-core 的项目
    pipeline_path = pipeline if "/" in pipeline or os.path.exists(pipeline) else f"nf-core/{pipeline}"

    # profile = kwargs.get("profile", "singularity")
    profile = DEFAULT_WORKFLOW_ARGS.get("profile", "singularity")
    input_file = os.path.abspath(_join_data_dir(base_data_dir, kwargs.get("input", "")))
    outdir = os.path.abspath(_join_data_dir(base_data_dir, kwargs.get("outdir", "nfcore_out")))

    # 构建基础命令
    cmd_parts = [
        "nextflow run",
        pipeline_path,
        f"-profile {profile}",
        f"-w {work_dir}",  # Nextflow 官方简写是 -w
        f"--input '{input_file}'",
        f"--outdir '{outdir}'",
        f"-singularity.cacheDir {IMAGE_PATH['image_store']}"
    ]

    # 添加配置和额外参数
    if kwargs.get("genome"):
        cmd_parts.append(f"--genome {kwargs['genome']}")
    if kwargs.get("config"):
        # -c 是指定配置文件
        cmd_parts.append(f"-c {os.path.abspath(kwargs['config'])}")
    if kwargs.get("extra_args"):
        cmd_parts.append(kwargs["extra_args"])

    return " ".join(cmd_parts)
