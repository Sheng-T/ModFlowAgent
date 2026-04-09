import os

from configs.path_config import PROJECT_ROOT
from utils.config_utils import load_tool_config

TOOL_LIST = ['dorado', 'samtools', 'modkit', 'fastqc', 'workflow']

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
        "name": "modkit",
        "description": (
            "modkit 是 ONT 官方的碱基修饰分析工具，用于处理 BAM 文件中的 m6A/5mC 等修饰信号。"
            "主要子命令：pileup（汇总为 bedMethyl）、extract（提取每条 read 的修饰）、"
            "summary（统计概览）、adjust-mods（调整修饰概率）。"
            "适用场景：dorado basecaller 输出后做甲基化位点统计。"
        ),
    },
    {
        "name": "fastqc",
        "description": (
            "FastQC 是测序数据质量控制工具，支持 FASTQ/BAM/SAM 输入，"
            "输出 HTML 报告，涵盖碱基质量、GC 含量、接头污染等多个质控模块。"
            "适用于对原始测序数据或比对结果进行快速质量检查。"
        ),
    },
    {
        "name": "workflow",
        "description": (
            "Nextflow/nf-core 端到端分析流水线，适合用户需要从原始数据到最终结果的完整分析，而不是单步操作。"
            "可用 pipeline 及其适用场景：\n"
            "- methylong：ONT 或 PacBio HiFi 数据的甲基化分析（输入 BAM/pod5 + 参考基因组）\n"
            "- rnaseq：RNA-seq 差异表达分析（输入 fastq）\n"
            "- methylseq：Bisulfite 甲基化测序分析（输入 fastq）\n"
            "- sarek：肿瘤/正常样本变异检测（输入 fastq）\n"
            "- ampliseq：扩增子测序/16S 分析（输入 fastq）\n"
            "- mag：宏基因组拼装与分箱（输入 fastq）\n"
            "- taxprofiler：宏基因组物种分类（输入 fastq/fasta）\n"
            "当用户描述的任务需要多个分析步骤、或明确提到'分析流程/流水线/pipeline'时，优先选择 workflow。"
        ),
    },
]

TOOL_ARGS = {
    "dorado":   load_tool_config(os.path.join(PROJECT_ROOT, "static/dorado/dorado_args.json")),
    "samtools": load_tool_config(os.path.join(PROJECT_ROOT, "static/samtools/samtools_args.json")),
    "modkit":   load_tool_config(os.path.join(PROJECT_ROOT, "static/modkit/modkit_args.json")),
    "fastqc":   load_tool_config(os.path.join(PROJECT_ROOT, "static/fastqc/fastqc_args.json")),
}





