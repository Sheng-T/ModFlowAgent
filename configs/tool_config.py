import os

from configs.path_config import PROJECT_ROOT
from utils.config_utils import load_tool_config

TOOL_LIST = ['dorado', 'samtools', 'workflow']

TOOL_DESCIPTION = [
    {
        "name": "dorado",
        "description": "Dorado is a high-performance, GPU-accelerated basecalling engine developed by Oxford Nanopore "
                       "Technologies that employs sophisticated deep learning architectures to transform raw ionic current "
                       "signals into high-fidelity nucleotide sequences while enabling the concurrent, real-time detection "
                       "of diverse epigenetic modifications (such as $m^6A$ and $5mC$).",
    },
    {
        "name": "samtools",
        "description": "Samtools serves as the definitive toolkit for the rapid manipulation and statistical analysis "
                       "of high-throughput sequencing data, offering a comprehensive array of subcommands for "
                       "coordinate-based sorting, indexing, format interconversion, and complex filtering of alignment "
                       "records stored in SAM, BAM, and CRAM specifications.",
    },
    {
        "name": "workflow",
        "description": "Nextflow orchestrates scalable workflow execution and is commonly used by nf-core pipelines; "
                       "it supports reproducible runs with singularity profiles and resumable execution.",
    },
]

TOOL_ARGS = {
    "dorado": load_tool_config(os.path.join(PROJECT_ROOT, "static/dorado/dorado_args.json")),
    "samtools": load_tool_config(os.path.join(PROJECT_ROOT, "static/samtools/samtools_args.json")),
    # "workflow": load_tool_config(os.path.join(PROJECT_ROOT, "static/workflow/nfcore_args.json")),
}

TOOLS_IMAGE = {
    "dorado": "dorado_latest.sif",
    "samtools": "samtools_1.16.1.sif",
    # "workflow": "nextflow_25_10_4.sif",
}




