
from tools.analyzers.functional.base import FunctionalAnalyzer


class MethylationAnalyzer(FunctionalAnalyzer):
    # 判断阈值
    HIGH_METH_THRESHOLD   = 60.0   
    LOW_METH_THRESHOLD    = 20.0   
    BIMODAL_STDEV_THRESH  = 30.0   

    def analyze(self, file_stats: dict) -> dict:
        if "error" in file_stats:
            return {"error": file_stats["error"]}

        mean  = file_stats.get("methylation_mean",  0.0)
        stdev = file_stats.get("methylation_stdev", 0.0)
        high_frac = file_stats.get("high_meth_fraction", 0.0)   # ≥80% 
        low_frac  = file_stats.get("low_meth_fraction",  0.0)   # <20% 

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
