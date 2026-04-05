import copy

from configs.workflow_config import pipeline_exists
from tools.workflow.command_builder import build_workflow_command


def validate_nfcore_kwargs(kwargs: dict) -> str | None:
    pipeline = kwargs.get("pipeline", "")
    if not pipeline:
        return "Error: nextflow nf-core requires kwargs['pipeline']."

    if not pipeline_exists(pipeline):
        return (
            "Error: unsupported nf-core pipeline. Supported pipelines: "
            "methylong, rnaseq, sarek, ampliseq, methylseq, mag, taxprofiler."
        )

    if not kwargs.get("input"):
        return "Error: nextflow nf-core requires kwargs['input'] (samplesheet)."

    if not kwargs.get("outdir"):
        return "Error: nextflow nf-core requires kwargs['outdir']."

    return None


def methylong(args_dict, data_path):
    """
    Verify and build nf-core/nextflow command.
    Called by WORKFLOW_REGISTRY with (tool_args, data_path).
    """
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})

    err = validate_nfcore_kwargs(kwargs)
    if err:
        return err

    return build_workflow_command(kwargs, data_path)
