"""
Universal MultiQC result parser.

Walks an outdir tree to find multiqc_data.json and pre-rendered PNG plots.
Used as a common base layer by all nf-core workflow analyzers.
"""
import json
import os


def find_multiqc_data_json(outdir: str) -> str | None:
    """Recursively search outdir for multiqc_data.json; return its path or None."""
    for root, _dirs, files in os.walk(outdir):
        if "multiqc_data.json" in files:
            return os.path.join(root, "multiqc_data.json")
    return None


def find_multiqc_pngs(outdir: str) -> list[str]:
    """
    Collect PNGs from multiqc_plots/png/ inside outdir.
    Falls back to any PNG directly inside any multiqc* directory.
    """
    pngs: list[str] = []
    for root, _dirs, files in os.walk(outdir):
        if os.path.basename(root) == "png" and "multiqc_plots" in root:
            for f in sorted(files):
                if f.endswith(".png"):
                    pngs.append(os.path.join(root, f))
    if not pngs:
        for root, _dirs, files in os.walk(outdir):
            if "multiqc" in os.path.basename(root).lower():
                for f in sorted(files):
                    if f.endswith(".png"):
                        pngs.append(os.path.join(root, f))
    return pngs


def parse_multiqc_json(json_path: str) -> dict:
    """
    Parse multiqc_data.json into a compact stats dict:
      general_stats    — {sample: {metric: value}}
      samtools_flagstat — raw flagstat section if present
      software_versions — {tool: version}
      sections          — list of available section names
    """
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to read multiqc_data.json: {e}"}

    result: dict = {}

    # General stats (list of dicts, one per module)
    merged: dict = {}
    for section in data.get("report_general_stats_data", []):
        if not isinstance(section, dict):
            continue
        for sample, metrics in section.items():
            if isinstance(metrics, dict):
                merged.setdefault(sample, {}).update(metrics)
    result["general_stats"] = merged

    saved = data.get("report_saved_raw_data", {})

    # Samtools flagstat
    flagstat = saved.get("multiqc_samtools_flagstat", {})
    if flagstat:
        result["samtools_flagstat"] = flagstat

    # Software versions
    versions: dict = {}
    for entry in saved.get("multiqc_software_versions", {}).values():
        if isinstance(entry, dict):
            versions.update(entry)
    result["software_versions"] = versions

    result["sections"] = list(saved.keys())
    return result
