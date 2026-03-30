DEFAULT_WORKFLOW_ARGS = {
    "profile": "singularity",
    "extra_args": "-resume -with-report -with-trace -with-timeline",
}


REQUIRED_FIELDS = ["pipeline", "input", "outdir"]

SUPPORTED_PIPELINES = [
    "methylong",
    "rnaseq",
    "sarek",
    "ampliseq",
    "methylseq",
    "mag",
    "taxprofiler",
]


def pipeline_exists(name: str) -> bool:
    return str(name).lower() in SUPPORTED_PIPELINES




