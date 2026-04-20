"""
BED / bedMethyl 文件统计分析器（纯 Python，支持 .gz 压缩）。

标准 bedMethyl 列（0-indexed，来自 modkit pileup）：
  0  chrom
  1  start (0-based)
  2  end
  3  name  (修饰类型，如 "m" / "a")
  4  score (0-1000)
  5  strand
  6  thickStart
  7  thickEnd
  8  color
  9  N_valid_cov      ← 覆盖度
  10 fraction_modified ← 甲基化率 (0-100)
"""
import gzip
import os
import statistics

from tools.analyzers.file.base import FileAnalyzer

_MIN_COVERAGE = 1   # 统计时过滤低覆盖位点的阈值


def _open(path: str):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path, "r")


class BedAnalyzer(FileAnalyzer):
    def analyze(self, file_path: str) -> dict:
        if not os.path.isfile(file_path):
            return {"error": f"File not found: {file_path}"}

        coverages: list[int]   = []
        meth_rates: list[float] = []
        chroms: set[str]       = set()
        total_sites            = 0
        skip_header            = 0

        try:
            with _open(file_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("track") or line.startswith("browser"):
                        skip_header += 1
                        continue

                    cols = line.split("\t")
                    if len(cols) < 11:
                        # 宽松处理：至少需要 coverage 列（col 9）
                        if len(cols) < 10:
                            continue
                    total_sites += 1
                    chroms.add(cols[0])

                    try:
                        cov = int(cols[9])
                    except (ValueError, IndexError):
                        cov = 0

                    coverages.append(cov)

                    if cov >= _MIN_COVERAGE and len(cols) >= 11:
                        try:
                            meth = float(cols[10])
                            meth_rates.append(meth)
                        except ValueError:
                            pass

        except Exception as e:
            return {"error": str(e)}

        if total_sites == 0:
            return {"file": os.path.basename(file_path), "type": "bed",
                    "total_sites": 0, "error": "File is empty or format mismatch"}

        result = {
            "file":        os.path.basename(file_path),
            "type":        "bed",
            "total_sites": total_sites,
            "chrom_count": len(chroms),
        }

        # ── 覆盖度分布 ──────────────────────────────────────────────────────────
        if coverages:
            cov_sorted = sorted(coverages)
            n = len(cov_sorted)
            result["coverage_mean"]    = round(statistics.mean(coverages), 2)
            result["coverage_median"]  = round(statistics.median(coverages), 2)
            result["coverage_p25"]     = round(cov_sorted[n // 4], 2)
            result["coverage_p75"]     = round(cov_sorted[3 * n // 4], 2)
            result["coverage_min"]     = cov_sorted[0]
            result["coverage_max"]     = cov_sorted[-1]
            result["sites_cov_ge1"]    = sum(1 for c in coverages if c >= 1)
            result["sites_cov_ge5"]    = sum(1 for c in coverages if c >= 5)
            result["sites_cov_ge10"]   = sum(1 for c in coverages if c >= 10)

        # ── 甲基化率分布 ────────────────────────────────────────────────────────
        if meth_rates:
            mr_sorted = sorted(meth_rates)
            n = len(mr_sorted)
            result["methylation_mean"]    = round(statistics.mean(meth_rates), 2)
            result["methylation_median"]  = round(statistics.median(meth_rates), 2)
            result["methylation_p25"]     = round(mr_sorted[n // 4], 2)
            result["methylation_p75"]     = round(mr_sorted[3 * n // 4], 2)
            result["methylation_stdev"]   = round(statistics.stdev(meth_rates), 2) if len(meth_rates) > 1 else 0.0
            result["sites_high_meth"]     = sum(1 for m in meth_rates if m >= 80)   # ≥80%
            result["sites_low_meth"]      = sum(1 for m in meth_rates if m < 20)    # <20%
            result["sites_medium_meth"]   = total_sites - result["sites_high_meth"] - result["sites_low_meth"]
            result["high_meth_fraction"]  = round(result["sites_high_meth"] / total_sites * 100, 2)
            result["low_meth_fraction"]   = round(result["sites_low_meth"]  / total_sites * 100, 2)

        return result
