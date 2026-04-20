DEFAULT_WORKFLOW_ARGS = {
    "profile": "singularity",
    "extra_args": "-resume -with-report -with-trace -with-timeline",
}

# nf-core 资源上限，防止单个 process 申请超出机器实际可用量。
# max_cpus=None 表示自动取 os.cpu_count()；显式设值可覆盖。
MAX_WORKFLOW_RESOURCES = {
    "max_cpus":   None,       # None → auto-detect
    "max_memory": "30.GB",
    "max_time":   "72.h",
}


REQUIRED_FIELDS = ["pipeline", "input", "outdir"]

SUPPORTED_PIPELINES = [
    "methylong",
]

# 流水线的用户可见描述，供 UI 展示
PIPELINE_DESCRIPTIONS = [
    {
        "name": "methylong",
        "short_description": "Long-read methylation calling pipeline, supports ONT / PacBio.",
        "description": "Methylong is a bioinformatics pipeline tailored for long-read methylation calling. "
            "This pipeline supports ONT or PacBio HiFi sequencing data, accepts basecalled BAM files or raw Pod5 reads, "
            "performs optional modification calling, read preprocessing, genome alignment, and methylation detection. "
            "Methylation outputs are provided in BED/BEDGRAPH format for downstream analysis including SNV calling, phasing, and DMR analysis.",
        "input": "BAM/pod5 + reference genome FASTA"
    }
]


def pipeline_exists(name: str) -> bool:
    return str(name).lower() in SUPPORTED_PIPELINES




