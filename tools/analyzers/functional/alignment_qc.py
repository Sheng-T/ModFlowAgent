"""
比对质量评级（适用于 mapping/alignment 工具产生的 BAM）。
输入：BamAnalyzer 返回的统计 dict。
"""
from tools.analyzers.functional.base import FunctionalAnalyzer


class AlignmentQCAnalyzer(FunctionalAnalyzer):
    # 判断阈值
    MAPPED_RATE_PASS    = 90.0   # mapped_rate ≥ 90% → PASS
    MAPPED_RATE_WARN    = 70.0   # 70% ≤ mapped_rate < 90% → WARNING
    MIN_READS_WARN      = 10000  # 总 reads 过少时额外警告

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        mapped_rate  = file_stats.get("mapped_rate",   0.0)
        total_reads  = file_stats.get("total_reads",   0)
        avg_quality  = file_stats.get("avg_quality",   None)

        issues = []

        # 映射率评级
        if mapped_rate >= self.MAPPED_RATE_PASS:
            grade = "PASS"
        elif mapped_rate >= self.MAPPED_RATE_WARN:
            grade = "WARNING"
            issues.append(f"映射率偏低 ({mapped_rate:.1f}%，建议 ≥90%)")
        else:
            grade = "FAIL"
            issues.append(f"映射率过低 ({mapped_rate:.1f}%)")

        # reads 数量检查
        if total_reads < self.MIN_READS_WARN:
            issues.append(f"reads 总数偏少 ({total_reads:,})")
            if grade == "PASS":
                grade = "WARNING"

        # 平均质量检查（仅当 samtools stats 成功时）
        if avg_quality is not None:
            if avg_quality < 7:
                issues.append(f"平均碱基质量偏低 (Q{avg_quality:.1f}，建议 ≥Q10)")
                if grade == "PASS":
                    grade = "WARNING"

        return {
            "module":       "alignment_qc",
            "grade":        grade,            # PASS / WARNING / FAIL
            "mapped_rate":  mapped_rate,
            "total_reads":  total_reads,
            "avg_quality":  avg_quality,
            "issues":       issues,
        }
