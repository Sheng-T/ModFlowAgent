"""
Basecall 质量评估（适用于 dorado basecaller 产生的 BAM）。
输入：BamAnalyzer 返回的统计 dict。
"""
from tools.analyzers.functional.base import FunctionalAnalyzer


class BasecallQCAnalyzer(FunctionalAnalyzer):
    # Nanopore basecall 质量阈值（基于 Q 值）
    Q_GOOD       = 15.0   # Q ≥ 15 → good（高精度）
    Q_ACCEPTABLE = 10.0   # Q ≥ 10 → acceptable
    # reads 通量阈值（示意，可按实际测序目标调整）
    MIN_READS_ACCEPTABLE = 1000

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        avg_quality    = file_stats.get("avg_quality",     None)
        avg_read_len   = file_stats.get("avg_read_length", None)
        total_reads    = file_stats.get("total_reads",     0)
        mapped_rate    = file_stats.get("mapped_rate",     None)

        issues = []

        # Q 值评级
        if avg_quality is None:
            quality_grade = "unknown"
            issues.append("Mean Q-score unavailable (samtools stats did not run or failed)")
        elif avg_quality >= self.Q_GOOD:
            quality_grade = "good"
        elif avg_quality >= self.Q_ACCEPTABLE:
            quality_grade = "acceptable"
            issues.append(f"Mean Q-score below recommended (Q{avg_quality:.1f}, recommended ≥Q15)")
        else:
            quality_grade = "poor"
            issues.append(f"Mean Q-score too low (Q{avg_quality:.1f})")

        # read count
        if total_reads < self.MIN_READS_ACCEPTABLE:
            issues.append(f"Read count low ({total_reads:,}), reliability may be limited")

        return {
            "module":          "basecall_qc",
            "quality_grade":   quality_grade,    # good / acceptable / poor / unknown
            "avg_quality":     avg_quality,
            "avg_read_length": avg_read_len,
            "total_reads":     total_reads,
            "mapped_rate":     mapped_rate,
            "issues":          issues,
        }
