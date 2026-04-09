"""
甲基化修饰模式判断。
输入：BedAnalyzer 返回的统计 dict。
输出：修饰模式（高甲基化 / 低甲基化 / 混合）及判断依据。
"""
from tools.analyzers.functional.base import FunctionalAnalyzer


class MethylationAnalyzer(FunctionalAnalyzer):
    # 判断阈值
    HIGH_METH_THRESHOLD   = 60.0   # mean ≥ 60% → 高甲基化
    LOW_METH_THRESHOLD    = 20.0   # mean < 20% → 低甲基化
    BIMODAL_STDEV_THRESH  = 30.0   # stdev ≥ 30 且 high/low 均显著 → 双峰/混合

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        mean  = file_stats.get("methylation_mean",  0.0)
        stdev = file_stats.get("methylation_stdev", 0.0)
        high_frac = file_stats.get("high_meth_fraction", 0.0)   # ≥80% 位点占比
        low_frac  = file_stats.get("low_meth_fraction",  0.0)   # <20% 位点占比

        # 双峰（混合）：高甲基化和低甲基化位点都超过 20%，且标准差大
        if (stdev >= self.BIMODAL_STDEV_THRESH
                and high_frac >= 20.0 and low_frac >= 20.0):
            pattern = "mixed"
            confidence = "high" if stdev >= 35 else "medium"
        elif mean >= self.HIGH_METH_THRESHOLD:
            pattern = "high"
            confidence = "high" if mean >= 80 else "medium"
        elif mean < self.LOW_METH_THRESHOLD:
            pattern = "low"
            confidence = "high" if mean < 10 else "medium"
        else:
            pattern = "intermediate"
            confidence = "medium"

        return {
            "module":     "methylation_pattern",
            "pattern":    pattern,          # high / low / intermediate / mixed
            "confidence": confidence,       # high / medium / low
            "mean_methylation":  mean,
            "stdev":             stdev,
            "high_meth_fraction": high_frac,
            "low_meth_fraction":  low_frac,
        }
