"""
ONT RNA local workflow analyzer.

Parses BAM (sorted.bam), modkit pileup (bedMethyl) and modkit extract
from step subdirectories and generates PNG visualizations + text summary.

Outputs:
  From sorted.bam  → bam_summary.png, read_length.png, quality_dist.png
  From pileup.bed  → freq_distribution.png, site_stats.png, coverage_dist.png
                     high_confidence_sites.csv
  From extract.tsv → mod_qual_dist.png, per_read_mod_count.png, seq_logo_<code>.png
  Text for LLM     → analysis_summary.txt  (all numeric results, human-readable)
"""
from __future__ import annotations

import os
from typing import Optional

from tools.analyzers.workflow.base import WorkflowAnalyzer
from utils.ui_logger import ui_print

# ── Modification code → human-readable name ───────────────────────────────────
# modkit reports modifications using either a single-letter SAM shorthand ("a", "m", …)
# or the numeric CHEBI code ("17596", "21891", …).  Both forms appear in the code column.
#
# RNA modifications
RNA_MOD_CODE_NAMES: dict[str, str] = {
    # single-letter SAM shorthands
    "a":     "m6A",           # N(6)-Methyladenosine        CHEBI:21891  SAM: A+a
    "m":     "m5C",           # 5-Methylcytosine            CHEBI:27551  SAM: C+m
    "h":     "5hmC",          # 5-Hydroxymethylcytosine     CHEBI:76792  SAM: C+h
    "f":     "5fC",           # 5-Formylcytosine            CHEBI:76793  SAM: C+f
    "c":     "5caC",          # 5-Carboxylcytosine          CHEBI:76794  SAM: C+c
    "b":     "5hmU",          # 5-Hydroxymethyluridine                   SAM: T+b
    "e":     "5fU",           # 5-Formyluridine                          SAM: T+e
    # numeric CHEBI codes
    "17596": "Inosine",       # Inosine                     CHEBI:17596  SAM: A+17596
    "17802": "Ψ (pseU)",      # Pseudouridine               CHEBI:17802  SAM: T+17802
    "19228": "2'-OmeC",       # 2'-O-methylcytidine         CHEBI:19228  SAM: C+19228
    "69426": "2'-OmeA",       # 2'-O-methyladenosine        CHEBI:69426  SAM: A+69426
    "19229": "2'-OmeG",       # 2'-O-methylguanosine        CHEBI:19229  SAM: G+19229
    "19227": "2'-OmeU",       # 2'-O-methyluridine          CHEBI:19227  SAM: T+19227
    "21891": "m6A",           # numeric alias for m6A       CHEBI:21891
}



# Default lookup used by this RNA analyzer
MOD_CODE_NAMES = RNA_MOD_CODE_NAMES

# bedMethyl column indices (no header row, 0-indexed)
_B_CHROM  = 0
_B_START  = 1
_B_CODE   = 3   # modification code
_B_COV    = 9   # N_valid_cov
_B_FRAC   = 10  # fraction_modified


def _mod_name(code: str) -> str:
    return MOD_CODE_NAMES.get(str(code).strip(), str(code))


def _fmt_count(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.0f}K"
    return str(int(v))


# ── Plot helpers ──────────────────────────────────────────────────────────────

def _save_fig(fig, png_path: str, plot_paths: list[str]) -> None:
    """Save figure as PNG (raster, for UI display) and PDF (vector, for publication).
    Appends the PNG path to plot_paths; PDF is saved alongside with the same stem."""
    fig.savefig(png_path, dpi=130, bbox_inches="tight")
    fig.savefig(png_path[:-4] + ".pdf", bbox_inches="tight")
    plot_paths.append(png_path)


# ── File discovery ─────────────────────────────────────────────────────────────

def _find_step_file(run_dir: str, filename: str) -> Optional[str]:
    """Return the first occurrence of `filename` inside any step* subdirectory."""
    if not run_dir or not os.path.isdir(run_dir):
        return None
    for entry in sorted(os.scandir(run_dir), key=lambda e: e.name):
        if entry.is_dir() and entry.name.startswith("step"):
            candidate = os.path.join(entry.path, filename)
            if os.path.isfile(candidate):
                return candidate
    return None


# ── bedMethyl (pileup.bed) analysis ───────────────────────────────────────────

def _analyze_pileup(bed_path: str, analysis_dir: str) -> tuple[list[str], dict, list[str]]:
    plot_paths: list[str] = []
    warnings:   list[str] = []
    stats:      dict      = {}

    try:
        import pandas as pd
    except ImportError:
        warnings.append("pandas not available — pileup analysis skipped")
        return plot_paths, stats, warnings

    # Limit rows to avoid OOM on very large ONT pileup files
    _MAX_ROWS = 5_000_000

    try:
        df = pd.read_csv(bed_path, sep="\t", header=None, low_memory=False, nrows=_MAX_ROWS)
        ui_print(f"[OntRnaAnalyzer] pileup.bed loaded: {len(df):,} rows × {df.shape[1]} cols")
        if df.shape[1] < 11:
            warnings.append(f"pileup.bed has only {df.shape[1]} columns, expected ≥13")
            return plot_paths, stats, warnings

        df[_B_COV]  = pd.to_numeric(df[_B_COV],  errors="coerce").fillna(0)
        df[_B_FRAC] = pd.to_numeric(df[_B_FRAC], errors="coerce").fillna(0)
        df[_B_CODE] = df[_B_CODE].astype(str).str.strip()

        codes = df[_B_CODE].unique().tolist()
        stats["modification_codes"] = {c: _mod_name(c) for c in codes}

        per_code: dict[str, dict] = {}
        for code in codes:
            sub    = df[df[_B_CODE] == code]
            cov5   = sub[_B_COV] >= 5
            hc     = cov5 & (sub[_B_FRAC] >= 0.8)
            covered_sub = sub.loc[cov5, _B_FRAC]
            per_code[code] = {
                "name":                 _mod_name(code),
                "total_sites":          len(sub),
                "covered_sites_ge5x":   int(cov5.sum()),
                "high_conf_sites":      int(hc.sum()),
                "mean_freq_ge5x":       round(float(covered_sub.mean()),   4) if not covered_sub.empty else 0.0,
                "median_freq_ge5x":     round(float(covered_sub.median()), 4) if not covered_sub.empty else 0.0,
            }
        stats["per_code"] = per_code

        # Save high-confidence sites for LLM consumption
        hc_mask = (df[_B_COV] >= 5) & (df[_B_FRAC] >= 0.8)
        hc_df   = df[hc_mask]
        if not hc_df.empty:
            hc_csv = os.path.join(analysis_dir, "high_confidence_sites.csv")
            hc_df.iloc[:, [_B_CHROM, _B_START, _B_CODE, _B_COV, _B_FRAC]].to_csv(
                hc_csv, index=False,
                header=["chrom", "start", "mod_code", "coverage", "fraction_modified"],
            )
            stats["high_conf_count"] = len(hc_df)
            stats["high_conf_csv"]   = hc_csv
        else:
            stats["high_conf_count"] = 0

    except Exception as e:
        warnings.append(f"Pileup parsing failed: {e}")
        stats["error"] = str(e)
        return plot_paths, stats, warnings

    # ── Plots ────────────────────────────────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    except ImportError:
        warnings.append("matplotlib not available — pileup plots skipped")
        return plot_paths, stats, warnings

    COLORS = ["#E05C5C", "#5B9BD5", "#6BBF6B", "#E0A050", "#9B5BD5"]

    try:
        # ── 1. Frequency distribution per modification code ──────────────────
        ncols = len(codes)
        fig, axes = plt.subplots(1, ncols, figsize=(4.5 * ncols, 3.5), squeeze=False)
        for ci, code in enumerate(codes):
            ax  = axes[0][ci]
            sub = df[(df[_B_CODE] == code) & (df[_B_COV] >= 5)][_B_FRAC]
            if sub.empty:
                ax.text(0.5, 0.5, "No sites ≥5×", ha="center", va="center", transform=ax.transAxes)
            else:
                sub_plot = sub.sample(200_000, random_state=42) if len(sub) > 200_000 else sub
                n, bins_e, patches = ax.hist(
                    sub_plot, bins=50, color=COLORS[ci % len(COLORS)],
                    alpha=0.75, edgecolor="white", linewidth=0.4,
                )
                # shade bins above threshold differently
                thresh_idx = next((i for i, b in enumerate(bins_e[1:]) if b >= 0.8), len(patches) - 1)
                for p in patches[thresh_idx:]:
                    p.set_facecolor(COLORS[ci % len(COLORS)])
                    p.set_alpha(0.95)
                ax.axvline(0.8, color="#c0392b", linestyle="--", linewidth=1.2, label="≥0.8 threshold")
                ax.legend(fontsize=7, framealpha=0.6)
                # log y if range is large
                if n.max() > 0 and n[n > 0].min() > 0 and n.max() / n[n > 0].min() > 50:
                    ax.set_yscale("log")
                    ax.set_ylabel("Sites (log scale)", fontsize=9)
                else:
                    ax.set_ylabel("Number of Sites", fontsize=9)
                ax.yaxis.set_major_formatter(mticker.FuncFormatter(
                    lambda x, _: f"{int(x):,}" if x >= 1 else f"{x:.0e}"
                ))
            ax.grid(axis="y", alpha=0.25, linewidth=0.6)
            ax.set_xlabel("Modification Fraction", fontsize=9)
            if sub.empty:
                ax.set_ylabel("Number of Sites", fontsize=9)
            ax.set_title(f"{_mod_name(code)}\n(sites ≥5× coverage)", fontsize=9)
            ax.set_xlim(0, 1)
        fig.suptitle("Modification Frequency Distribution", fontsize=11, y=1.02)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "freq_distribution.png")
        _save_fig(fig, out, plot_paths)
        plt.close(fig)
    except Exception as e:
        warnings.append(f"Freq distribution plot failed: {e}")

    try:
        # ── 2. Site statistics grouped bar ───────────────────────────────────
        labels     = [_mod_name(c) for c in codes]
        total_v    = [per_code[c]["total_sites"]        for c in codes]
        cov5_v     = [per_code[c]["covered_sites_ge5x"] for c in codes]
        hc_v       = [per_code[c]["high_conf_sites"]    for c in codes]

        x = list(range(len(codes)))
        w = 0.25
        fig, ax = plt.subplots(figsize=(max(4, 2.2 * len(codes) + 1.5), 3.5))
        b1 = ax.bar([xi - w for xi in x], total_v, width=w, label="Total Sites",           color="#8FAADC")
        b2 = ax.bar([xi     for xi in x], cov5_v,  width=w, label="≥5× Coverage",          color="#5B9BD5")
        b3 = ax.bar([xi + w for xi in x], hc_v,    width=w, label="High-Conf (≥5×, ≥0.8)", color="#E05C5C")
        for bars in (b1, b2, b3):
            ax.bar_label(bars, labels=[_fmt_count(v) for v in bars.datavalues],
                         padding=2, fontsize=7)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel("Number of Sites", fontsize=9)
        ax.set_title("Site-level Summary by Modification Type", fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _fmt_count(v)))
        ax.set_ylim(0, max(total_v) * 1.25 if total_v else 1)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "site_stats.png")
        _save_fig(fig, out, plot_paths)
        plt.close(fig)
    except Exception as e:
        warnings.append(f"Site stats plot failed: {e}")

    try:
        # ── 3. Coverage distribution ─────────────────────────────────────────
        cov_vals = df[_B_COV].clip(upper=200)
        cov_plot = cov_vals.sample(200_000, random_state=42) if len(cov_vals) > 200_000 else cov_vals
        fig, ax  = plt.subplots(figsize=(4.5, 3.2))
        ax.hist(cov_plot, bins=50, color="#5B9BD5", alpha=0.85, edgecolor="none")
        ax.axvline(5, color="crimson", linestyle="--", linewidth=1, label="5× threshold")
        ax.legend(fontsize=8)
        ax.set_xlabel("Site Coverage Depth (capped at 200×)", fontsize=9)
        ax.set_ylabel("Number of Sites", fontsize=9)
        ax.set_title("Site Coverage Distribution", fontsize=10)
        fig.tight_layout()
        out = os.path.join(analysis_dir, "coverage_dist.png")
        _save_fig(fig, out, plot_paths)
        plt.close(fig)
    except Exception as e:
        warnings.append(f"Coverage plot failed: {e}")

    return plot_paths, stats, warnings


# ── modkit extract TSV analysis ───────────────────────────────────────────────

def _analyze_extract(tsv_path: str, analysis_dir: str) -> tuple[list[str], dict, list[str]]:
    plot_paths: list[str] = []
    warnings:   list[str] = []
    stats:      dict      = {}

    try:
        import pandas as pd
    except ImportError:
        warnings.append("pandas not available — extract analysis skipped")
        return plot_paths, stats, warnings

    _MAX_ROWS = 2_000_000   # limit memory for large ONT extract files

    try:
        df = pd.read_csv(tsv_path, sep="\t", low_memory=False, nrows=_MAX_ROWS)
        df.columns = [c.strip() for c in df.columns]
        ui_print(f"[OntRnaAnalyzer] extract.tsv loaded: {len(df):,} rows × {df.shape[1]} cols")
        all_cols   = set(df.columns)

        # Column aliases across modkit versions
        qual_col    = next((c for c in ["mod_qual", "mod_probability"]         if c in all_cols), None)
        code_col    = next((c for c in ["mod_codebase_qual", "mod_code"]       if c in all_cols), None)
        kmer_col    = next((c for c in ["query_kmer"]                          if c in all_cols), None)
        read_col    = next((c for c in ["read_id"]                             if c in all_cols), None)

        stats["total_calls"] = len(df)
        stats["total_reads"] = int(df[read_col].nunique()) if read_col else None

        if qual_col:
            mod_q = pd.to_numeric(df[qual_col], errors="coerce").dropna()
            # Normalize to 0-1 if values appear to be 0-255
            if mod_q.max() > 1:
                mod_q = mod_q / 255.0
            stats["mean_mod_qual"]   = round(float(mod_q.mean()), 4)
            stats["frac_high_conf"]  = round(float((mod_q >= 0.8).mean()), 4)

        if code_col:
            per_code: dict[str, dict] = {}
            for code, grp in df.groupby(code_col):
                code_s = str(code).strip()
                if qual_col:
                    q = pd.to_numeric(grp[qual_col], errors="coerce").dropna()
                    if q.max() > 1:
                        q = q / 255.0
                    per_code[code_s] = {
                        "name":       _mod_name(code_s),
                        "n_calls":    len(grp),
                        "mean_qual":  round(float(q.mean()), 4),
                        "n_high_conf": int((q >= 0.8).sum()),
                    }
                else:
                    per_code[code_s] = {"name": _mod_name(code_s), "n_calls": len(grp)}
            stats["per_code"] = per_code

    except Exception as e:
        warnings.append(f"Extract parsing failed: {e}")
        stats["error"] = str(e)
        return plot_paths, stats, warnings

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    except ImportError:
        warnings.append("matplotlib not available — extract plots skipped")
        return plot_paths, stats, warnings

    COLORS = ["#E05C5C", "#5B9BD5", "#6BBF6B", "#E0A050"]

    try:
        # ── 1. Modification quality distribution per code ─────────────────────
        if qual_col and code_col:
            codes = df[code_col].dropna().unique().tolist()
            ncols = len(codes)
            fig, axes = plt.subplots(1, ncols, figsize=(4.5 * ncols, 3.2), squeeze=False)
            for ci, code in enumerate(codes):
                ax  = axes[0][ci]
                sub = df[df[code_col] == code]
                q   = pd.to_numeric(sub[qual_col], errors="coerce").dropna()
                if q.max() > 1:
                    q = q / 255.0
                q_plot = q.sample(200_000, random_state=42) if len(q) > 200_000 else q
                ax.hist(q_plot, bins=50, color=COLORS[ci % len(COLORS)], alpha=0.85, edgecolor="none")
                ax.axvline(0.8, color="crimson", linestyle="--", linewidth=1, label="threshold 0.8")
                ax.legend(fontsize=7)
                ax.set_xlabel("Modification Probability", fontsize=9)
                ax.set_ylabel("Number of Calls", fontsize=9)
                ax.set_title(f"{_mod_name(str(code))}", fontsize=9)
                ax.set_xlim(0, 1)
            fig.suptitle("Per-read Modification Quality Distribution", fontsize=11, y=1.02)
            fig.tight_layout()
            out = os.path.join(analysis_dir, "mod_qual_dist.png")
            _save_fig(fig, out, plot_paths)
            plt.close(fig)
    except Exception as e:
        warnings.append(f"Quality dist plot failed: {e}")

    try:
        # ── 2. Per-read modification count distribution ───────────────────────
        if read_col:
            per_read = df.groupby(read_col).size()
            max_bin  = min(int(per_read.max()) + 1, 100)
            pr_vals  = per_read.values
            pr_plot  = per_read.sample(200_000, random_state=42).values if len(per_read) > 200_000 else pr_vals
            fig, ax  = plt.subplots(figsize=(4.5, 3.2))
            ax.hist(pr_plot, bins=max_bin, color="#5B9BD5", alpha=0.85, edgecolor="none")
            ax.set_xlabel("Modifications per Read", fontsize=9)
            ax.set_ylabel("Number of Reads", fontsize=9)
            ax.set_title("Per-read Modification Count", fontsize=10)
            median_v = per_read.median()
            ax.axvline(median_v, color="crimson", linestyle="--", linewidth=1,
                       label=f"median = {median_v:.1f}")
            ax.legend(fontsize=8)
            fig.tight_layout()
            out = os.path.join(analysis_dir, "per_read_mod_count.png")
            _save_fig(fig, out, plot_paths)
            plt.close(fig)
    except Exception as e:
        warnings.append(f"Per-read count plot failed: {e}")

    # ── 3. Sequence logo ──────────────────────────────────────────────────────
    if kmer_col and code_col:
        _generate_seq_logos(df, code_col, kmer_col, analysis_dir, plot_paths, warnings)

    return plot_paths, stats, warnings


def _generate_seq_logos(df, code_col, kmer_col,
                        analysis_dir: str,
                        plot_paths: list[str],
                        warnings: list[str]) -> None:
    """Build a sequence logo + 5-mer motif bar chart for each modification code."""
    try:
        import logomaker
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    except ImportError as e:
        warnings.append(f"Sequence logo skipped — missing package: {e}. Install with: pip install logomaker")
        return

    import numpy as np

    BASES       = list("ACGT")

    def _compute_ic_df(counts_df: "pd.DataFrame") -> "pd.DataFrame":
        """Convert per-position base counts to information-content (bits) matrix.
        Each cell = freq * IC_pos, where IC_pos = log2(4) - H(pos).
        Negative values clipped to 0 (small-sample correction artefacts)."""
        freq = counts_df.div(counts_df.sum(axis=1), axis=0).fillna(0.25)
        entropy = -(freq * np.log2(freq + 1e-9)).sum(axis=1)
        ic_per_pos = np.log2(4) - entropy          # max 2 bits
        ic_df = freq.multiply(ic_per_pos.clip(lower=0), axis=0)
        return ic_df.clip(lower=0)

    codes = df[code_col].dropna().unique().tolist()
    for code in codes:
        safe_code = str(code).replace("/", "_").replace(" ", "_")
        mod_label = _mod_name(str(code))
        try:
            sub   = df[df[code_col] == code]
            kmers = sub[kmer_col].dropna().astype(str).str.upper().str.replace("U", "T")
            kmers = kmers[kmers.str.match(r"^[ACGT]{5}$")]

            if len(kmers) < 50:
                warnings.append(f"Too few valid k-mers for {mod_label} logo ({len(kmers)} found, need ≥50)")
                continue

            # Top-20 motif counts (full dataset, before sampling)
            kmer_counts  = kmers.value_counts()
            top20        = kmer_counts.head(20)

            # Cap sample for logo — stable after ~50k kmers
            kmers_logo = kmers.sample(50_000, random_state=42) if len(kmers) > 50_000 else kmers

            # Vectorized count matrix → IC matrix
            counts = pd.DataFrame(0, index=range(5), columns=BASES, dtype=float)
            for pos in range(5):
                vc = kmers_logo.str[pos].value_counts()
                for base in BASES:
                    counts.loc[pos, base] = vc.get(base, 0)
            ic_df = _compute_ic_df(counts)

            # ── Sequence logo (IC-scaled letter heights) ──────────────────────
            fig, ax = plt.subplots(figsize=(5, 2.8))
            logomaker.Logo(ic_df, ax=ax, color_scheme="classic")
            ax.set_xticks(range(5))
            ax.set_xticklabels(["-2", "-1", "0", "+1", "+2"], fontsize=9)
            ax.set_xlabel("Position relative to modification site", fontsize=9)
            ax.set_ylabel("Information content (bits)", fontsize=9)
            ax.set_ylim(bottom=0)
            ax.set_title(f"{mod_label} Sequence Context Logo (±2 bp)", fontsize=10)
            fig.tight_layout()
            out_logo = os.path.join(analysis_dir, f"seq_logo_{safe_code}.png")
            _save_fig(fig, out_logo, plot_paths)
            plt.close(fig)

            # ── Top-20 5-mer motif bar chart ─────────────────────────────────
            if len(top20) > 0:
                labels  = top20.index.tolist()
                values  = top20.values.tolist()
                # Color each bar by the center base (position 2) of the motif
                colors  = [BASE_COLORS.get(m[2], "#AAAAAA") for m in labels]
                h       = max(3.2, len(labels) * 0.35)
                fig2, ax2 = plt.subplots(figsize=(6, h))
                bars = ax2.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.65)
                ax2.bar_label(bars, fmt="%d", padding=3, fontsize=8)
                ax2.set_xlabel("Count", fontsize=9)
                ax2.set_title(f"{mod_label} Top-20 5-mer Motifs (center = modification site)", fontsize=10)
                ax2.set_xlim(0, max(values) * 1.15)
                ax2.tick_params(axis="y", labelsize=8)
                ax2.tick_params(axis="x", labelsize=8)
                fig2.tight_layout()
                out_motif = os.path.join(analysis_dir, f"motif_top20_{safe_code}.png")
                _save_fig(fig2, out_motif, plot_paths)
                plt.close(fig2)

        except Exception as e:
            warnings.append(f"Seq logo for {mod_label} failed: {e}")


# ── BAM QC analysis ───────────────────────────────────────────────────────────

def _analyze_bam(run_dir: str, analysis_dir: str) -> tuple[list[str], dict, list[str]]:
    """
    Find sorted.bam in step dirs and run a FAST flagstat-only check.
    Deliberately avoids `samtools stats` because it scans every read and
    can block for tens of minutes on large ONT files, stalling the whole
    summary thread and triggering Streamlit health-check failures.
    """
    plot_paths: list[str] = []
    warnings:   list[str] = []
    stats:      dict      = {}

    bam_path = _find_step_file(run_dir, "sorted.bam")
    if not bam_path:
        warnings.append("sorted.bam not found — BAM QC skipped")
        return plot_paths, stats, warnings

    try:
        from tools.analyzers.file.bam_analyzer import (
            _build_singularity_cmd, _run, _parse_flagstat,
        )
        cmd = _build_singularity_cmd(bam_path, f"flagstat {bam_path}")
        out, err = _run(cmd, timeout=30)   # flagstat is fast even on large files
        if out:
            stats = _parse_flagstat(out)
            stats["file"] = os.path.basename(bam_path)
            stats["type"] = "bam"
        else:
            warnings.append(f"samtools flagstat produced no output: {err[:200]}")
    except Exception as e:
        warnings.append(f"BAM flagstat failed: {e}")
        return plot_paths, stats, warnings

    # Quick mapping-rate pie chart from flagstat data only
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        total   = stats.get("total_reads", 0)
        mapped  = stats.get("mapped_reads") or stats.get("primary_mapped", 0)
        if total > 0:
            unmapped = total - mapped
            fig, ax  = plt.subplots(figsize=(4, 4))
            ax.pie(
                [mapped, unmapped],
                labels=[f"Mapped\n{mapped:,}", f"Unmapped\n{unmapped:,}"],
                colors=["#4C9BE8", "#E87B4C"],
                autopct="%1.1f%%",
                startangle=90,
                textprops={"fontsize": 9},
            )
            rate = stats.get("mapped_rate", round(mapped / total * 100, 2))
            ax.set_title(f"Mapping Rate: {rate}%", fontsize=10)
            fig.tight_layout()
            out_path = os.path.join(analysis_dir, "bam_mapping.png")
            _save_fig(fig, out_path, plot_paths)
            plt.close(fig)
    except Exception as e:
        warnings.append(f"BAM mapping plot failed: {e}")

    return plot_paths, stats, warnings


# ── Text summary for LLM ──────────────────────────────────────────────────────

def _write_text_summary(summary: dict, plot_paths: list[str], analysis_dir: str) -> str:
    """
    Write analysis_summary.txt — human-readable numeric results for LLM consumption.
    Returns the path to the written file, or empty string on failure.
    """
    lines: list[str] = ["=== ONT RNA Modification Analysis Summary ===\n"]

    # ── BAM QC ────────────────────────────────────────────────────────────────
    bam = summary.get("bam", {})
    if bam and not bam.get("error"):
        lines.append("## BAM Quality Control")
        lines.append(f"  Total reads      : {bam.get('total_reads', 'N/A')}")
        lines.append(f"  Mapped reads     : {bam.get('mapped_reads', 'N/A')}  ({bam.get('mapped_rate', 'N/A')}%)")
        lines.append(f"  Avg read quality : {bam.get('avg_quality', 'N/A')}")
        lines.append(f"  Avg read length  : {bam.get('avg_read_length', 'N/A')} bp")
        lines.append("")

    # ── bedMethyl (pileup) ────────────────────────────────────────────────────
    pileup = summary.get("pileup", {})
    if pileup and not pileup.get("error"):
        lines.append("## Site-level Modification Statistics (bedMethyl / pileup)")
        per_code = pileup.get("per_code", {})
        for code, info in per_code.items():
            name = info.get("name", code)
            lines.append(f"  [{name}]")
            lines.append(f"    Total sites           : {info.get('total_sites', 'N/A')}")
            lines.append(f"    Sites ≥5× coverage    : {info.get('covered_sites_ge5x', 'N/A')}")
            lines.append(f"    High-conf sites       : {info.get('high_conf_sites', 'N/A')}  (freq≥0.8 & cov≥5×)")
            lines.append(f"    Mean freq (≥5× sites) : {info.get('mean_freq_ge5x', 'N/A')}")
            lines.append(f"    Median freq (≥5×)     : {info.get('median_freq_ge5x', 'N/A')}")
        hcc = pileup.get("high_conf_count")
        if hcc is not None:
            lines.append(f"  Total high-confidence sites (all codes): {hcc}")
        lines.append("")

    # ── modkit extract (read-level) ───────────────────────────────────────────
    extract = summary.get("extract", {})
    if extract and not extract.get("error"):
        lines.append("## Read-level Modification Statistics (modkit extract)")
        lines.append(f"  Total calls      : {extract.get('total_calls', 'N/A')}")
        lines.append(f"  Unique reads     : {extract.get('total_reads', 'N/A')}")
        lines.append(f"  Mean mod quality : {extract.get('mean_mod_qual', 'N/A')}")
        lines.append(f"  High-conf frac   : {extract.get('frac_high_conf', 'N/A')}  (qual≥0.8)")
        per_code = extract.get("per_code", {})
        if per_code:
            lines.append("  Per-code breakdown:")
            for code, info in per_code.items():
                name = info.get("name", code)
                lines.append(f"    [{name}]  calls={info.get('n_calls', 'N/A')}  "
                             f"mean_qual={info.get('mean_qual', 'N/A')}  "
                             f"high_conf={info.get('n_high_conf', 'N/A')}")
        lines.append("")

    # ── Generated plots list ──────────────────────────────────────────────────
    if plot_paths:
        lines.append("## Generated Visualization Files")
        for p in plot_paths:
            lines.append(f"  - {os.path.basename(p)}")
        lines.append("")

    out_path = os.path.join(analysis_dir, "analysis_summary.txt")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return out_path
    except Exception:
        return ""


# ── Analyzer class ─────────────────────────────────────────────────────────────

class OntRnaAnalyzer(WorkflowAnalyzer):
    """
    Analyzer for ont_rna local workflow.
    `outdir` = run_dir containing step01_…/ … step07_…/ subdirectories.
    """

    def analyze(self, outdir: str, analysis_dir: str) -> dict:
        plot_paths: list[str] = []
        warnings:   list[str] = []
        summary:    dict      = {}

        os.makedirs(analysis_dir, exist_ok=True)
        ui_print("[OntRnaAnalyzer] Starting analysis…")

        # BAM QC (sorted.bam in step dirs)
        ui_print("[OntRnaAnalyzer] Step 1/4 — BAM QC (samtools flagstat)")
        bp, bs, bw = _analyze_bam(outdir, analysis_dir)
        plot_paths.extend(bp)
        if bs:
            summary["bam"] = bs
        warnings.extend(bw)
        ui_print(f"[OntRnaAnalyzer] BAM QC done: {len(bp)} plot(s)")

        pileup_bed  = _find_step_file(outdir, "pileup.bed")
        extract_tsv = _find_step_file(outdir, "extract.tsv")

        if pileup_bed:
            ui_print(f"[OntRnaAnalyzer] Step 2/4 — pileup.bed analysis ({os.path.getsize(pileup_bed) // 1024 // 1024} MB)")
            pp, ps, pw = _analyze_pileup(pileup_bed, analysis_dir)
            plot_paths.extend(pp)
            summary["pileup"] = ps
            warnings.extend(pw)
            ui_print(f"[OntRnaAnalyzer] pileup done: {len(pp)} plot(s)")
        else:
            ui_print("[OntRnaAnalyzer] Step 2/4 — pileup.bed not found, skipped")
            warnings.append("pileup.bed not found — reference may not have been provided")

        if extract_tsv:
            ui_print(f"[OntRnaAnalyzer] Step 3/4 — extract.tsv analysis ({os.path.getsize(extract_tsv) // 1024 // 1024} MB)")
            ep, es, ew = _analyze_extract(extract_tsv, analysis_dir)
            plot_paths.extend(ep)
            summary["extract"] = es
            warnings.extend(ew)
            ui_print(f"[OntRnaAnalyzer] extract done: {len(ep)} plot(s)")
        else:
            ui_print("[OntRnaAnalyzer] Step 3/4 — extract.tsv not found, skipped")
            warnings.append("extract.tsv not found")

        if outdir and os.path.isdir(outdir):
            summary["completed_steps"] = sorted(
                e.name for e in os.scandir(outdir)
                if e.is_dir() and e.name.startswith("step")
            )

        # Write text summary for LLM
        ui_print("[OntRnaAnalyzer] Step 4/4 — writing text summary & generating LLM report")
        txt_path = _write_text_summary(summary, plot_paths, analysis_dir)

        return {
            "workflow":           "ont_rna",
            "summary":            summary,
            "plot_paths":         plot_paths,
            "warnings":           warnings,
            "text_summary_path":  txt_path,
        }
