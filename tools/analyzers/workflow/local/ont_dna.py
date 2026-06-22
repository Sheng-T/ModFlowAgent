"""
ONT DNA local workflow analyzer.

Parses modkit pileup (bedMethyl) and modkit extract output from step
subdirectories and generates PNG visualizations.

  From pileup.bed  → top_regions_bar.png, site_coverage_bar.png
  From extract.tsv → read_modification_pie.png
"""
from __future__ import annotations

import glob
import os

from tools.analyzers.workflow.base import WorkflowAnalyzer

# DNA modifications
DNA_MOD_CODE_NAMES: dict[str, str] = {
    # single-letter SAM shorthands
    "m":     "5mC",           # 5-Methylcytosine            CHEBI:27551  SAM: C+m
    "h":     "5hmC",          # 5-Hydroxymethylcytosine     CHEBI:76792  SAM: C+h
    "f":     "5fC",           # 5-Formylcytosine            CHEBI:76793  SAM: C+f
    "c":     "5caC",          # 5-Carboxylcytosine          CHEBI:76794  SAM: C+c
    "a":     "6mA",           # 6-Methyladenine             CHEBI:28871  SAM: A+a
    # numeric CHEBI codes
    "21839": "4mC",           # N(4)-methylcytosine         CHEBI:21839  SAM: C+21839
    "28871": "6mA",           # numeric alias for 6mA       CHEBI:28871
    "76792": "5hmC",          # numeric alias for 5hmC      CHEBI:76792
}

def _mod_name(code: str) -> str:
    return DNA_MOD_CODE_NAMES.get(str(code).strip(), str(code))


def _parse_bedmethyl(bed_path: str) -> dict:
    """
    bedMethyl columns (0-indexed):
      0=chrom  1=start  2=end  3=mod_code  4=score  5=strand
      9=N_valid_cov  10=fraction_modified  11=N_mod  12=N_canonical
    """
    try:
        import pandas as pd
        df = pd.read_csv(bed_path, sep="\t", header=None, low_memory=False)
        if df.shape[1] < 11:
            return {"parse_error": "unexpected column count"}

        cov_col  = 9
        frac_col = 10
        chr_col  = 0

        total_sites   = len(df)
        covered_sites = int((df[cov_col] >= 1).sum())
        hc_sites      = int(((df[cov_col] >= 5) & (df[frac_col] >= 0.5)).sum())
        top_chroms = (
            df[df[cov_col] >= 5]
            .groupby(chr_col)[frac_col]
            .mean()
            .nlargest(5)
            .round(4)
            .to_dict()
        )
        return {
            "total_sites":           total_sites,
            "covered_sites":         covered_sites,
            "high_confidence_sites": hc_sites,
            "top_regions_mean_frac": {str(k): float(v) for k, v in top_chroms.items()},
        }
    except Exception as e:
        return {"parse_error": str(e)}


def _parse_extract(extract_path: str) -> dict:
    """
    modkit extract --full produces a TSV with per-read modification calls.
    Column names vary by modkit version — located by header.
    """
    try:
        import pandas as pd
        df = pd.read_csv(extract_path, sep="\t", low_memory=False)
        cols_lower = {c.lower(): c for c in df.columns}

        total_calls = len(df)
        mod_col = next(
            (cols_lower[c] for c in ["is_modified", "modified", "mod_qual"] if c in cols_lower),
            None,
        )
        n_mod = int((df[mod_col].astype(float) >= 0.5).sum()) if mod_col else None
        return {
            "total_read_calls":  total_calls,
            "n_modified":        n_mod,
            "fraction_modified": round(n_mod / total_calls, 4) if n_mod is not None and total_calls else None,
        }
    except Exception as e:
        return {"parse_error": str(e)}


def _generate_plots(summary: dict, analysis_dir: str, warnings: list) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        warnings.append("matplotlib not available — charts skipped")
        return []

    plt.rcParams.update({"font.size": 9})
    paths: list[str] = []

    # ── 1. Read-level modification pie ────────────────────────────────────────
    extract = summary.get("extract_stats", {})
    total   = extract.get("total_read_calls")
    n_mod   = extract.get("n_modified")
    if total and n_mod is not None and "parse_error" not in extract:
        n_unmod = total - n_mod
        fig, ax = plt.subplots(figsize=(4, 3.2))
        wedges, _, autotexts = ax.pie(
            [n_mod, n_unmod],
            autopct="%1.1f%%",
            colors=["#E05C5C", "#5B9BD5"],
            startangle=90,
            pctdistance=0.78,
            wedgeprops={"linewidth": 0.5, "edgecolor": "white"},
        )
        for t in autotexts:
            t.set_fontsize(8)
        ax.legend(wedges, ["Modified", "Unmodified"],
                  loc="lower center", bbox_to_anchor=(0.5, -0.12),
                  ncol=2, fontsize=8, frameon=False)
        ax.set_title("Read-level Modification Calls", fontsize=10, pad=6)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "read_modification_pie.png")
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        paths.append(out)

    # ── 2. Top regions bar ────────────────────────────────────────────────────
    pileup = summary.get("pileup_stats", {})
    top    = pileup.get("top_regions_mean_frac", {})
    if top and "parse_error" not in pileup:
        labels = [str(k)[:28] for k in top.keys()]
        values = list(top.values())
        h      = max(2.4, len(labels) * 0.48)
        fig, ax = plt.subplots(figsize=(5, h))
        bars = ax.barh(labels, values, color="#5B9BD5", height=0.55)
        ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
        ax.set_xlabel("Mean Modification Fraction", fontsize=9)
        ax.set_title("Top Regions by Modification Fraction", fontsize=10)
        ax.set_xlim(0, max(values) * 1.3)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=8)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "top_regions_bar.png")
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        paths.append(out)

    # ── 3. Site coverage summary ──────────────────────────────────────────────
    total_s   = pileup.get("total_sites")
    covered_s = pileup.get("covered_sites")
    hc_s      = pileup.get("high_confidence_sites")
    if total_s and covered_s is not None and "parse_error" not in pileup:
        cats   = ["Total\nSites", "Covered\n(≥1×)", "High-conf\n(≥5×,≥50%)"]
        counts = [total_s, covered_s, hc_s or 0]
        fig, ax = plt.subplots(figsize=(4, 3))
        bars = ax.bar(cats, counts, color=["#8FAADC", "#5B9BD5", "#2E75B6"], width=0.5)

        def _fmt(v: float, _=None) -> str:
            if v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            if v >= 1_000:
                return f"{v/1_000:.0f}K"
            return str(int(v))

        ax.bar_label(bars, labels=[_fmt(c) for c in counts], padding=3, fontsize=8)
        ax.set_ylabel("Number of Sites", fontsize=9)
        ax.set_title("Site-level Coverage Summary", fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt))
        ax.tick_params(labelsize=8)
        ax.set_ylim(0, max(counts) * 1.18)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "site_coverage_bar.png")
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        paths.append(out)

    return paths


class OntDnaAnalyzer(WorkflowAnalyzer):
    """Analyzer for the ont_dna local workflow."""

    def analyze(self, outdir: str, analysis_dir: str) -> dict:
        summary: dict      = {}
        plot_paths: list   = []
        warnings: list     = []

        if not outdir or not os.path.isdir(outdir):
            warnings.append(f"Output directory not found: {outdir}")
            return {"workflow": "ont_dna", "summary": summary,
                    "plot_paths": plot_paths, "warnings": warnings}

        # ── pileup (bedMethyl) ────────────────────────────────────────────────
        pileup_candidates = (
            glob.glob(os.path.join(outdir, "*pileup*", "*.bed"))
            + glob.glob(os.path.join(outdir, "*pileup*", "*.bedMethyl"))
            + glob.glob(os.path.join(outdir, "*pileup*", "*.bed.gz"))
        )
        if pileup_candidates:
            pf = pileup_candidates[0]
            summary["pileup_file"]  = os.path.relpath(pf, outdir)
            summary["pileup_stats"] = _parse_bedmethyl(pf)
            if "parse_error" in summary["pileup_stats"]:
                warnings.append(f"Could not parse pileup file: {summary['pileup_stats']['parse_error']}")
        else:
            summary["pileup_file"] = None

        # ── extract (per-read TSV) ────────────────────────────────────────────
        extract_candidates = (
            glob.glob(os.path.join(outdir, "*extract*", "*.tsv"))
            + glob.glob(os.path.join(outdir, "*extract*", "*.bed"))
            + glob.glob(os.path.join(outdir, "*extract*", "*.txt"))
        )
        if extract_candidates:
            ef = extract_candidates[0]
            summary["extract_file"]  = os.path.relpath(ef, outdir)
            summary["extract_stats"] = _parse_extract(ef)
            if "parse_error" in summary["extract_stats"]:
                warnings.append(f"Could not parse extract file: {summary['extract_stats']['parse_error']}")
        else:
            summary["extract_file"] = None
            warnings.append("modkit extract output not found — pipeline may not have completed.")

        summary["completed_steps"] = sorted(
            e.name for e in os.scandir(outdir)
            if e.is_dir() and e.name.startswith("step")
        )

        os.makedirs(analysis_dir, exist_ok=True)
        plot_paths = _generate_plots(summary, analysis_dir, warnings)

        return {
            "workflow":   "ont_dna",
            "summary":    summary,
            "plot_paths": plot_paths,
            "warnings":   warnings,
        }
