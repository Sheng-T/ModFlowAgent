"""
CpG 位点覆盖度评估。
输入：BedAnalyzer 返回的统计 dict。
"""
from tools.analyzers.functional.base import FunctionalAnalyzer


class CpGSiteAnalyzer(FunctionalAnalyzer):
    # 评估阈值
    COV_SUFFICIENT    = 10    # 中位覆盖度 ≥ 10x → sufficient
    COV_MARGINAL      = 5     # 中位覆盖度 ≥ 5x  → marginal
    SITE_MIN_10X_FRAC = 0.5   # ≥10x 位点占比 ≥ 50% → sufficient

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        total_sites   = file_stats.get("total_sites",    0)
        cov_median    = file_stats.get("coverage_median", 0.0)
        cov_mean      = file_stats.get("coverage_mean",   0.0)
        sites_ge10    = file_stats.get("sites_cov_ge10",  0)
        sites_ge5     = file_stats.get("sites_cov_ge5",   0)
        sites_ge1     = file_stats.get("sites_cov_ge1",   0)

        issues = []

        # 覆盖度充分性评估
        ge10_frac = sites_ge10 / total_sites if total_sites > 0 else 0.0

        if cov_median >= self.COV_SUFFICIENT and ge10_frac >= self.SITE_MIN_10X_FRAC:
            assessment = "sufficient"
        elif cov_median >= self.COV_MARGINAL:
            assessment = "marginal"
            issues.append(f"Median coverage low ({cov_median:.1f}x, recommended ≥10x)")
        else:
            assessment = "insufficient"
            issues.append(f"Coverage insufficient (median {cov_median:.1f}x, only {ge10_frac*100:.1f}% sites ≥10x)")

        # site count check
        if total_sites < 100_000:
            issues.append(f"Few CpG sites detected ({total_sites:,}), may affect global methylation assessment")

        return {
            "module":            "cpg_site_coverage",
            "assessment":        assessment,      # sufficient / marginal / insufficient
            "coverage_median":   cov_median,
            "coverage_mean":     cov_mean,
            "total_sites":       total_sites,
            "sites_cov_ge1":     sites_ge1,
            "sites_cov_ge5":     sites_ge5,
            "sites_cov_ge10":    sites_ge10,
            "ge10_fraction_pct": round(ge10_frac * 100, 2),
            "issues":            issues,
        }
