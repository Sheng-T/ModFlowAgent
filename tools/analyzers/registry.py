"""
两张独立注册表：
  FILE_ANALYZER_REGISTRY    — 后缀 → FileAnalyzer 实例
  FUNCTIONAL_ANALYZER_MENU  — 供 LLM 选择的功能分析菜单
"""
import os
import re

from tools.analyzers.file.bam_analyzer    import BamAnalyzer
from tools.analyzers.file.bed_analyzer    import BedAnalyzer
from tools.analyzers.file.vcf_analyzer    import VcfAnalyzer

from tools.analyzers.functional.methylation   import MethylationAnalyzer
from tools.analyzers.functional.alignment_qc  import AlignmentQCAnalyzer
from tools.analyzers.functional.basecall_qc   import BasecallQCAnalyzer
from tools.analyzers.functional.cpg_site      import CpGSiteAnalyzer


# ── 文件分析注册表（后缀 → 实例）──────────────────────────────────────────────
FILE_ANALYZER_REGISTRY: dict = {
    ".bam":    BamAnalyzer(),
    ".bed":    BedAnalyzer(),
    ".bed.gz": BedAnalyzer(),
    ".vcf":    VcfAnalyzer(),
    ".vcf.gz": VcfAnalyzer(),
}


def get_file_analyzer(file_path: str):
    """根据文件路径后缀返回对应的 FileAnalyzer，找不到返回 None。"""
    name = os.path.basename(file_path).lower()
    for suffix, analyzer in FILE_ANALYZER_REGISTRY.items():
        if name.endswith(suffix):
            return analyzer
    return None


# ── 功能分析菜单（LLM 从此列表中选择）────────────────────────────────────────
FUNCTIONAL_ANALYZER_MENU: list[dict] = [
    {
        "name":        "methylation_pattern",
        "description": "Analyse methylation modification patterns in BED/bedMethyl files; classify as hypermethylated / hypomethylated / mixed",
        "triggered_by": ["methylation", "methylong", "m6a", "5mc", "mod", "bed"],
        "required_stat_type": "bed",
        "analyzer":    MethylationAnalyzer(),
    },
    {
        "name":        "alignment_qc",
        "description": "Assess BAM alignment quality (mapping rate, read count); suitable for minimap2 / STAR output",
        "triggered_by": ["align", "map", "minimap", "star", "mapping", "alignment"],
        "required_stat_type": "bam",
        "analyzer":    AlignmentQCAnalyzer(),
    },
    {
        "name":        "basecall_qc",
        "description": "Evaluate Nanopore basecalling BAM quality (Q-score, read length); suitable for dorado basecaller output",
        "triggered_by": ["basecall", "dorado", "nanopore", "ont", "basecalling"],
        "required_stat_type": "bam",
        "analyzer":    BasecallQCAnalyzer(),
    },
    {
        "name":        "cpg_site_coverage",
        "description": "Assess whether CpG site coverage is sufficient; suitable for BED output from methylation pipelines",
        "triggered_by": ["cpg", "methylation", "methyllong", "methylong", "coverage"],
        "required_stat_type": "bed",
        "analyzer":    CpGSiteAnalyzer(),
    },
]


def get_functional_analyzer(name: str):
    """按 name 查找功能 analyzer 实例，找不到返回 None。"""
    for item in FUNCTIONAL_ANALYZER_MENU:
        if item["name"] == name:
            return item["analyzer"]
    return None


# ── 输出文件路径提取（从 shell 命令字符串）────────────────────────────────────

def extract_output_paths(commands: list[str]) -> list[str]:
    """
    从 pending_commands 中提取输出文件路径。
    支持：
      - stdout 重定向：... > /path/to/file
      - -o / --output 标志：-o /path/to/file  或  --output /path/to/file
      - --outdir 标志（取目录，后续扫描目录内文件）
    """
    paths = []
    for cmd in commands:
        # stdout 重定向
        for m in re.finditer(r'>\s*([^\s"\'|&;]+)', cmd):
            p = m.group(1)
            if not p.startswith("-"):
                paths.append(p)
        # -o / --output(-file)
        for m in re.finditer(r'(?:^|\s)(?:-o|--output(?:-file)?)\s+([^\s"\']+)', cmd):
            p = m.group(1)
            if not p.startswith("-"):
                paths.append(p)
    return list(dict.fromkeys(paths))   # 去重保序
