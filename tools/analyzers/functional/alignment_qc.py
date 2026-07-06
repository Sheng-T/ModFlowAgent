
from tools.analyzers.functional.base import FunctionalAnalyzer


class AlignmentQCAnalyzer(FunctionalAnalyzer):
    # 判断阈值
    MAPPED_RATE_PASS    = 90.0   # mapped_rate ≥ 90% → PASS
    MAPPED_RATE_WARN    = 70.0   # 70% ≤ mapped_rate < 90% → WARNING
    MIN_READS_WARN      = 10000  

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        mapped_rate  = file_stats.get("mapped_rate",   0.0)
        total_reads  = file_stats.get("total_reads",   0)
        avg_quality  = file_stats.get("avg_quality",   None)

        issues = []

        if mapped_rate >= self.MAPPED_RATE_PASS:
            grade = "PASS"
        elif mapped_rate >= self.MAPPED_RATE_WARN:
            grade = "WARNING"
            issues.append(f"Mapping rate low ({mapped_rate:.1f}%, recommended ≥90%)")
        else:
            grade = "FAIL"
            issues.append(f"Mapping rate critically low ({mapped_rate:.1f}%)")

        # read count check
        if total_reads < self.MIN_READS_WARN:
            issues.append(f"Total reads low ({total_reads:,})")
            if grade == "PASS":
                grade = "WARNING"

        # average quality check (only when samtools stats succeeded)
        if avg_quality is not None:
            if avg_quality < 7:
                issues.append(f"Mean base quality low (Q{avg_quality:.1f}, recommended ≥Q10)")
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
