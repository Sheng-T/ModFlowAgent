import os


def _join_data_dir(base_data_dir: str, p: str) -> str:
    if not p:
        return p
    return os.path.join(base_data_dir, os.path.basename(str(p)))


def build_nfcore_command(kwargs: dict, data_path: dict) -> str:
    base_data_dir = os.path.expanduser(data_path.get("base_data_dir", "~/agent_data"))
    work_dir = os.path.expanduser(data_path.get("work_dir", "~/agent_data/nextflow_work"))

    pipeline = kwargs.get("pipeline", "").lower()
    profile = kwargs.get("profile", "singularity")
    input_file = _join_data_dir(base_data_dir, kwargs.get("input", ""))
    outdir = _join_data_dir(base_data_dir, kwargs.get("outdir", "nfcore_out"))
    genome = kwargs.get("genome", "")
    config = kwargs.get("config", "")
    extra_args = kwargs.get("extra_args", "")

    cmd_parts = [
        f"nextflow run nf-core/{pipeline}",
        f"-profile {profile}",
        f"--input {input_file}",
        f"--outdir {outdir}",
        f"-work-dir {work_dir}",
    ]

    if genome:
        cmd_parts.append(f"--genome {genome}")
    if config:
        cmd_parts.append(f"-c {config}")
    if extra_args:
        cmd_parts.append(extra_args)

    return " ".join(cmd_parts)
