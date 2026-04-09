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
        "description": "分析 BED/bedMethyl 文件中的甲基化修饰模式，判断高甲基化/低甲基化/混合模式",
        "triggered_by": ["methylation", "methylong", "m6a", "5mc", "修饰", "甲基化", "mod", "bed"],
        "required_stat_type": "bed",
        "analyzer":    MethylationAnalyzer(),
    },
    {
        "name":        "alignment_qc",
        "description": "评估 BAM 文件的比对质量（映射率、reads 数量），适用于 minimap2/STAR 等比对工具的输出",
        "triggered_by": ["align", "map", "minimap", "star", "mapping", "比对", "alignment"],
        "required_stat_type": "bam",
        "analyzer":    AlignmentQCAnalyzer(),
    },
    {
        "name":        "basecall_qc",
        "description": "评估 Nanopore basecalling BAM 的碱基质量（Q 值、读长），适用于 dorado basecaller 输出",
        "triggered_by": ["basecall", "dorado", "nanopore", "ont", "碱基识别", "basecalling"],
        "required_stat_type": "bam",
        "analyzer":    BasecallQCAnalyzer(),
    },
    {
        "name":        "cpg_site_coverage",
        "description": "评估 CpG 位点覆盖度是否充分，适用于甲基化分析流程的 BED 输出",
        "triggered_by": ["cpg", "methylation", "methyllong", "methylong", "coverage", "覆盖度"],
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
