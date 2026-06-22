import os

from configs.path_config import PROJECT_ROOT
from utils.config_utils import load_tool_config

TOOL_LIST = ['dorado', 'samtools', 'modkit', 'fastqc', 'workflow']

TOOL_DESCRIPTION = [
    {
        "name": "dorado",
        "short_description": "ONT basecalling & modification detection",
        "description": "Dorado is a high-performance, GPU-accelerated basecalling engine developed by Oxford Nanopore "
                       "Technologies that employs sophisticated deep learning architectures to transform raw ionic current "
                       "signals into high-fidelity nucleotide sequences while enabling the concurrent, real-time detection "
                       "of diverse epigenetic modifications (such as $m^6A$ and $5mC$).",
    },
    {
        "name": "samtools",
        "short_description": "SAM/BAM manipulation & statistics",
        "description": "Samtools serves as the definitive toolkit for the rapid manipulation and statistical analysis "
                       "of high-throughput sequencing data, offering a comprehensive array of subcommands for "
                       "coordinate-based sorting, indexing, format interconversion, and complex filtering of alignment "
                       "records stored in SAM, BAM, and CRAM specifications.",
    },
    {
        "name": "modkit",
        "short_description": "ONT base modification analysis (m6A/5mC)",
        "description": (
            "modkit is the official base modification analysis tool from Oxford Nanopore Technologies (ONT), "
            "designed to process modification signals including m6A/5mC in BAM files. "
            "Key subcommands: pileup (summarize into bedMethyl format), extract (extract modifications per read), "
            "summary (generate statistical overview), adjust-mods (adjust modification probabilities). "
            "Application scenario: methylation site statistics after dorado basecaller output."
        ),
    },
    {
        "name": "fastqc",
        "short_description": "Sequencing data quality control",
        "description": (
            "FastQC is a sequencing data quality control tool that supports FASTQ/BAM/SAM input formats. "
            "It generates HTML reports covering multiple quality control modules including base quality, GC content, "
            "adapter contamination, and more. "
            "Suitable for rapid quality inspection of raw sequencing data or alignment results."
        ),
    },
    {
        "name": "workflow",
        "short_description": "End-to-end analysis workflows (nf-core or local)",
        "description": (
            "End-to-end multi-step analysis workflows, covering both nf-core/Nextflow pipelines and "
            "lightweight local chains of per-tool Singularity images. "
            "Choose 'workflow' when the user's task requires multiple analysis steps, "
            "or they explicitly mention 'pipeline / workflow / 流水线'. "
            "The agent will present all available workflows with descriptions and a recommendation "
            "so the user can select the best fit."
        ),
    },
]

# backward-compat alias (old code uses the typo)
TOOL_DESCIPTION = TOOL_DESCRIPTION

TOOL_ARGS = {
    "dorado":   load_tool_config(os.path.join(PROJECT_ROOT, "static/tools/dorado/dorado_args.json")),
    "samtools": load_tool_config(os.path.join(PROJECT_ROOT, "static/tools/samtools/samtools_args.json")),
    "modkit":   load_tool_config(os.path.join(PROJECT_ROOT, "static/tools/modkit/modkit_args.json")),
    "fastqc":   load_tool_config(os.path.join(PROJECT_ROOT, "static/tools/fastqc/fastqc_args.json")),
}
