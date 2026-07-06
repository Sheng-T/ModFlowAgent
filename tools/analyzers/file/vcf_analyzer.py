"""
 VCF 
  0  CHROM
  1  POS
  2  ID
  3  REF
  4  ALT
  5  QUAL
  6  FILTER   
  7  INFO
  8+ FORMAT
"""
import gzip
import os
from collections import Counter

from tools.analyzers.file.base import FileAnalyzer


def _open(path: str):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path, "r")


class VcfAnalyzer(FileAnalyzer):
    def analyze(self, file_path: str) -> dict:
        if not os.path.isfile(file_path):
            return {"error": f"File not found: {file_path}"}

        total_variants  = 0
        pass_variants   = 0
        filter_counts: Counter = Counter()
        chroms: set[str]       = set()
        var_types: Counter     = Counter()   # SNV / INDEL / MNV

        try:
            with _open(file_path) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    cols = line.split("\t")
                    if len(cols) < 5:
                        continue

                    total_variants += 1
                    chroms.add(cols[0])

                    filt = cols[6].strip() if len(cols) > 6 else "."
                    if filt == "PASS":
                        pass_variants += 1
                    filter_counts[filt] += 1

                    ref = cols[3]
                    alt = cols[4].split(",")[0]  
                    if len(ref) == 1 and len(alt) == 1:
                        var_types["SNV"] += 1
                    elif len(ref) != len(alt):
                        var_types["INDEL"] += 1
                    else:
                        var_types["MNV"] += 1

        except Exception as e:
            return {"error": str(e)}

        result = {
            "file":            os.path.basename(file_path),
            "type":            "vcf",
            "total_variants":  total_variants,
            "pass_variants":   pass_variants,
            "chrom_count":     len(chroms),
            "snv_count":       var_types.get("SNV", 0),
            "indel_count":     var_types.get("INDEL", 0),
            "mnv_count":       var_types.get("MNV", 0),
        }
        if total_variants > 0:
            result["pass_rate"] = round(pass_variants / total_variants * 100, 2)
        else:
            result["pass_rate"] = 0.0

        # 前5个常见 FILTER 值
        result["filter_summary"] = dict(filter_counts.most_common(5))

        return result
