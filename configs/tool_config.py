import json
import os

from configs.path_config import PROJECT_ROOT


def load_tool_config(file_name):
    # 获取当前文件所在目录，确保路径正确
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "tool_configs", file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


TOOL_LIST = ['dorado', 'samtools', 'nextflow']

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
        "name": "nextflow",
        "description": "Nextflow orchestrates scalable workflow execution and is commonly used by nf-core pipelines; "
                       "it supports reproducible runs with singularity profiles and resumable execution.",
    },
]

TOOL_ARGS = {
    "dorado": load_tool_config(os.path.join(PROJECT_ROOT, "static/dorado/dorado_args.json")),
    "samtools": load_tool_config(os.path.join(PROJECT_ROOT, "static/samtools/samtools_args.json")),
    "nextflow": load_tool_config(os.path.join(PROJECT_ROOT, "static/nfcore/nfcore_args.json")),
}

TOOLS_IMAGE = {
    "dorado": "dorado_latest.sif",
    "samtools": "samtools_1.16.1.sif",
    "nextflow": "nextflow_25_10_4.sif",
}

