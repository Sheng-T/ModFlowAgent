DEFAULT_WORKFLOW_ARGS = {
    "profile": "singularity",
    "extra_args": "-resume -with-report -with-trace -with-timeline",
}


REQUIRED_FIELDS = ["pipeline", "input", "outdir"]

SUPPORTED_PIPELINES = [
    "methylong",
]

# 流水线的用户可见描述，供 UI 展示
PIPELINE_DESCRIPTIONS = {
    "methylong": ("ONT / PacBio HiFi 甲基化分析", "输入：BAM + 参考基因组 FASTA"),
}


def pipeline_exists(name: str) -> bool:
    return str(name).lower() in SUPPORTED_PIPELINES




