"""
methylong workflow result analyzer.

Handles both ONT (modkit pileup, fraction 0-1) and PacBio (pb-CpG-tools,
percent 0-100) pileup formats with auto-detection.

Plots generated:
  mapping/         — per-sample mapping pie
  methylation/     — methylation distribution + CpG coverage histogram
  dmr/             — DMR count per chromosome bar chart
  haplotype/       — haplotype methylation comparison (hap1 vs hap2 scatter)
"""
import gzip
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from tools.analyzers.workflow.base import WorkflowAnalyzer
from tools.analyzers.workflow.nf.multiqc_parser import (
    find_multiqc_data_json,
    find_multiqc_pngs,
    parse_multiqc_json,
)

_C = {
    "mapped":   "#4C9BE8",
    "unmapped": "#E87B4C",
    "hyper":    "#E84C6B",
    "hypo":     "#4CE8A0",
    "mid":      "#F5A623",
    "hap1":     "#E05C5C",
    "hap2":     "#5B9BD5",
    "bg":       "#F8F9FA",
    "grid":     "#E0E0E0",
    "text":     "#2C3E50",
}

plt.rcParams.update({
    "axes.facecolor":   _C["bg"],
    "figure.facecolor": "white",
    "axes.grid":        True,
    "grid.color":       _C["grid"],
    "grid.linewidth":   0.8,
    "font.size":        11,
})


# ── helpers ───────────────────────────────────────────────────────────────────

def _savefig(fig, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _parse_flagstat(path: str) -> dict:
    stats: dict = {}
    try:
        with open(path) as f:
            for line in f:
                parts = line.strip().split(" + ")
                if len(parts) < 2:
                    continue
                count = int(parts[0])
                label = parts[1].split(None, 1)[-1].split("(")[0].strip()
                if "in total" in label:
                    stats["total"] = count
                elif "primary mapped" in label:
                    stats["primary_mapped"] = count
                elif label.startswith("mapped"):
                    stats.setdefault("mapped", count)
    except Exception:
        pass
    return stats


def _parse_bed_gz(path: str, max_lines: int = 300_000) -> dict:
    """Parse a pileup BED file. Auto-detects modkit (0-1) vs pb-CpG-tools (0-100)."""
    total = covered = 0
    cov:  list[int]   = []
    raw_fracs: list[float] = []

    try:
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                cols = line.strip().split("\t")
                if len(cols) < 10 or cols[0].startswith("#"):
                    continue
                try:
                    c    = int(cols[9])
                    frac = float(cols[10]) if len(cols) > 10 else 0.0
                except (ValueError, IndexError):
                    continue
                total += 1
                cov.append(c)
                raw_fracs.append(frac)
                if c >= 5:
                    covered += 1
    except Exception as e:
        return {"error": str(e)}

    if not raw_fracs:
        return {"total_sites": total, "covered_sites": covered}

    # Auto-detect: pb-CpG-tools encodes percent (0-100), modkit uses fraction (0-1)
    is_percent = max(raw_fracs) > 1.0
    fracs = np.array(raw_fracs)
    if is_percent:
        fracs = fracs / 100.0

    # Only report stats for covered sites (cov >= 5)
    cov_arr = np.array(cov)
    meth_covered = fracs[cov_arr >= 5]

    if len(meth_covered) == 0:
        return {"total_sites": total, "covered_sites": covered,
                "format": "percent" if is_percent else "fraction"}

    return {
        "total_sites":         total,
        "covered_sites":       covered,
        "coverage_rate_pct":   round(covered / total * 100, 2) if total else 0,
        "mean_methylation":    round(float(meth_covered.mean()), 4),
        "median_methylation":  round(float(np.median(meth_covered)), 4),
        "hypermethylated_pct": round(float((meth_covered >= 0.8).mean() * 100), 2),
        "hypomethylated_pct":  round(float((meth_covered <= 0.2).mean() * 100), 2),
        "format":              "percent" if is_percent else "fraction",
        "_meth_sample":        meth_covered[:5000].tolist(),
        "_cov_sample":         cov[:5000],
    }


def _parse_dss_dmr(path: str) -> list[dict]:
    """Parse DSS callDMR.txt → list of DMR dicts with chr/start/end/diff."""
    dmrs: list[dict] = []
    try:
        with open(path) as f:
            header = f.readline().strip().split()
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                row = dict(zip(header, parts))
                try:
                    dmrs.append({
                        "chr":        row.get("chr", ""),
                        "start":      int(row.get("start", 0)),
                        "end":        int(row.get("end", 0)),
                        "nCG":        int(float(row.get("nCG", 0))),
                        "meanMethy1": float(row.get("meanMethy1", 0)),
                        "meanMethy2": float(row.get("meanMethy2", 0)),
                        "diff":       float(row.get("diff.Methy", 0)),
                    })
                except (ValueError, KeyError):
                    continue
    except Exception:
        pass
    return dmrs


def _parse_hap_beds(hap_dir: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Parse haplotype modkit bed files (_1.bed, _2.bed).
    Returns (hap1_fracs, hap2_fracs) arrays aligned by position.
    """
    beds = sorted(f for f in os.listdir(hap_dir) if f.endswith(".bed") and not f.endswith("ungrouped.bed"))
    hap1_file = next((f for f in beds if f.endswith("_1.bed")), None)
    hap2_file = next((f for f in beds if f.endswith("_2.bed")), None)
    if not hap1_file or not hap2_file:
        return np.array([]), np.array([])

    def _read(fname: str) -> dict:
        pos_frac: dict = {}
        try:
            with open(os.path.join(hap_dir, fname)) as f:
                for line in f:
                    cols = line.strip().split("\t")
                    if len(cols) < 11 or cols[0].startswith("#"):
                        continue
                    try:
                        key  = (cols[0], int(cols[1]))
                        cov  = int(cols[9])
                        frac = float(cols[10])
                        if frac > 1:
                            frac /= 100.0
                        if cov >= 5:
                            pos_frac[key] = frac
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass
        return pos_frac

    d1 = _read(hap1_file)
    d2 = _read(hap2_file)
    common = sorted(set(d1) & set(d2))
    if not common:
        return np.array([]), np.array([])
    h1 = np.array([d1[k] for k in common])
    h2 = np.array([d2[k] for k in common])
    return h1, h2


# ── plot functions ─────────────────────────────────────────────────────────────

def _plot_mapping(fs: dict, sample: str, out_dir: str) -> str:
    total    = fs.get("total", 0)
    mapped   = fs.get("primary_mapped", fs.get("mapped", 0))
    unmapped = max(0, total - mapped)
    if total == 0:
        return ""
    pairs = [(v, l, c) for v, l, c in [
        (mapped,   f"Mapped ({mapped:,})",   _C["mapped"]),
        (unmapped, f"Unmapped ({unmapped:,})", _C["unmapped"]),
    ] if v > 0]
    if not pairs:
        return ""
    vs, ls, cs = zip(*pairs)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(vs, colors=cs, autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
           startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5})
    ax.legend(ls, loc="lower center", bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9)
    ax.set_title(f"Mapping — {sample}\n(total {total:,})", color=_C["text"])
    return _savefig(fig, os.path.join(out_dir, f"{sample}_mapping.png"))


def _plot_methylation(bed: dict, sample: str, out_dir: str) -> list[str]:
    paths: list[str] = []
    arr = np.array(bed.get("_meth_sample", []))
    if arr.size == 0:
        return paths

    # ── methylation distribution histogram ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    n, bins, patches = ax.hist(arr, bins=50, edgecolor="white", linewidth=0.3)
    for patch, left in zip(patches, bins[:-1]):
        patch.set_facecolor(_C["hyper"] if left >= 0.8 else
                            _C["hypo"]  if left <= 0.2 else _C["mid"])
    ax.legend(handles=[
        mpatches.Patch(color=_C["hyper"], label="≥80% (hyper)"),
        mpatches.Patch(color=_C["mid"],   label="20–80% (intermediate)"),
        mpatches.Patch(color=_C["hypo"],  label="≤20% (hypo)"),
    ], fontsize=8)
    mean_v = float(arr.mean())
    ax.axvline(mean_v, color=_C["text"], linestyle="--", linewidth=1.5,
               label=f"Mean = {mean_v:.3f}")
    ax.set_xlabel("Methylation Fraction (coverage ≥5×)")
    ax.set_ylabel("CpG Site Count")
    ax.set_title(f"Methylation Distribution — {sample}")
    fig.tight_layout()
    paths.append(_savefig(fig, os.path.join(out_dir, f"{sample}_methylation_dist.png")))

    # ── coverage histogram ─────────────────────────────────────────────────────
    cov_vals = bed.get("_cov_sample", [])
    if cov_vals:
        cv = np.array(cov_vals)
        cap = int(np.percentile(cv, 98)) + 1
        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.hist(cv[cv <= cap], bins=50, color=_C["mapped"],
                 edgecolor="white", linewidth=0.3, alpha=0.85)
        ax2.axvline(5, color=_C["unmapped"], linestyle="--",
                    linewidth=1.5, label="Min depth = 5×")
        ax2.set_xlabel("Read Depth per CpG Site")
        ax2.set_ylabel("Site Count")
        ax2.set_title(f"CpG Site Coverage — {sample}")
        ax2.legend(fontsize=9)
        fig2.tight_layout()
        paths.append(_savefig(fig2, os.path.join(out_dir, f"{sample}_cpg_coverage.png")))

    return paths


def _plot_dmr(dmrs: list[dict], sample: str, out_dir: str) -> list[str]:
    if not dmrs:
        return []
    paths: list[str] = []

    # ── DMR count per chromosome bar chart ────────────────────────────────────
    from collections import Counter
    chr_counts = Counter(d["chr"] for d in dmrs)
    # Keep standard chroms, sort numerically
    def _chr_key(c: str) -> tuple:
        c = c.replace("chr", "")
        return (0, int(c)) if c.isdigit() else (1, c)
    chroms = sorted(chr_counts, key=_chr_key)
    counts = [chr_counts[c] for c in chroms]

    fig, ax = plt.subplots(figsize=(max(6, len(chroms) * 0.45), 4))
    bars = ax.bar(chroms, counts, color=_C["hap1"], width=0.7)
    ax.bar_label(bars, padding=2, fontsize=7)
    ax.set_xlabel("Chromosome")
    ax.set_ylabel("DMR Count")
    ax.set_title(f"DMR Distribution per Chromosome — {sample}\n(total {len(dmrs):,} DMRs)")
    ax.tick_params(axis="x", labelsize=7, rotation=45)
    fig.tight_layout()
    paths.append(_savefig(fig, os.path.join(out_dir, f"{sample}_dmr_per_chrom.png")))

    # ── DMR methylation diff distribution ─────────────────────────────────────
    diffs = np.array([abs(d["diff"]) for d in dmrs])
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.hist(diffs, bins=40, color=_C["hap2"], edgecolor="white", linewidth=0.3)
    ax2.axvline(float(diffs.mean()), color=_C["text"], linestyle="--",
                linewidth=1.5, label=f"Mean |Δ| = {diffs.mean():.3f}")
    ax2.set_xlabel("|Methylation Difference| (Hap1 − Hap2)")
    ax2.set_ylabel("DMR Count")
    ax2.set_title(f"DMR Effect Size Distribution — {sample}")
    ax2.legend(fontsize=9)
    fig2.tight_layout()
    paths.append(_savefig(fig2, os.path.join(out_dir, f"{sample}_dmr_effect_size.png")))

    return paths


def _plot_haplotype(h1: np.ndarray, h2: np.ndarray, sample: str, out_dir: str) -> list[str]:
    if h1.size == 0 or h2.size == 0:
        return []
    paths: list[str] = []

    # ── scatter: hap1 vs hap2 methylation ─────────────────────────────────────
    # Subsample for speed
    idx = np.random.default_rng(42).choice(len(h1), min(len(h1), 20000), replace=False)
    x, y = h1[idx], h2[idx]

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.hexbin(x, y, gridsize=60, cmap="Blues", mincnt=1)
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Haplotype 1 Methylation")
    ax.set_ylabel("Haplotype 2 Methylation")
    ax.set_title(f"Haplotype Methylation — {sample}\n({len(h1):,} common CpG sites)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.tight_layout()
    paths.append(_savefig(fig, os.path.join(out_dir, f"{sample}_haplotype_scatter.png")))

    # ── violin: hap1 vs hap2 distribution ────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    vp = ax2.violinplot([h1, h2], positions=[1, 2], showmedians=True, showextrema=False)
    for body, color in zip(vp["bodies"], [_C["hap1"], _C["hap2"]]):
        body.set_facecolor(color); body.set_alpha(0.7)
    vp["cmedians"].set_color(_C["text"])
    ax2.set_xticks([1, 2])
    ax2.set_xticklabels(["Haplotype 1", "Haplotype 2"])
    ax2.set_ylabel("Methylation Fraction")
    ax2.set_title(f"Haplotype Methylation Distribution — {sample}")
    fig2.tight_layout()
    paths.append(_savefig(fig2, os.path.join(out_dir, f"{sample}_haplotype_violin.png")))

    return paths


# ── main analyzer ──────────────────────────────────────────────────────────────

class MethylongAnalyzer(WorkflowAnalyzer):

    def analyze(self, outdir: str, analysis_dir: str) -> dict:
        plot_paths: list[str] = []
        warnings:   list[str] = []
        summary:    dict      = {}

        # ── MultiQC universal layer ───────────────────────────────────────────
        mq_json = find_multiqc_data_json(outdir)
        if mq_json:
            summary["multiqc"] = parse_multiqc_json(mq_json)
        else:
            warnings.append("multiqc_data.json not found")
        plot_paths.extend(find_multiqc_pngs(outdir))

        # ── Per-sample analysis ───────────────────────────────────────────────
        per_sample: dict = {}

        for platform in os.listdir(outdir):
            platform_path = os.path.join(outdir, platform)
            if not os.path.isdir(platform_path) or platform in ("multiqc", "pipeline_info"):
                continue

            for sample in os.listdir(platform_path):
                sample_path = os.path.join(platform_path, sample)
                if not os.path.isdir(sample_path):
                    continue
                s: dict = {}

                # ── flagstat → mapping pie ────────────────────────────────────
                flagstat_dir = os.path.join(sample_path, "alignment", "flagstat")
                if os.path.isdir(flagstat_dir):
                    for fname in os.listdir(flagstat_dir):
                        if fname.endswith(".flagstat"):
                            fs = _parse_flagstat(os.path.join(flagstat_dir, fname))
                            if fs:
                                s["flagstat"] = fs
                                p = _plot_mapping(fs, sample,
                                                  os.path.join(analysis_dir, "mapping"))
                                if p:
                                    plot_paths.append(p)

                # ── pileup → methylation distribution + coverage ──────────────
                pileup_dir = os.path.join(sample_path, "pileup")
                if os.path.isdir(pileup_dir):
                    # Prefer combined file; fall back to positive strand
                    bed_files = [f for f in os.listdir(pileup_dir)
                                 if f.endswith(".bed.gz") or f.endswith(".bed")]
                    combined = next((f for f in bed_files
                                     if "positive" not in f and "negative" not in f), None)
                    chosen   = combined or next(
                        (f for f in bed_files if "positive" in f), None
                    ) or (bed_files[0] if bed_files else None)

                    if chosen:
                        bed = _parse_bed_gz(os.path.join(pileup_dir, chosen))
                        if "error" not in bed:
                            s["methylation"] = {k: v for k, v in bed.items()
                                                if not k.startswith("_")}
                            plot_paths.extend(_plot_methylation(
                                bed, sample, os.path.join(analysis_dir, "methylation")))
                            if bed.get("coverage_rate_pct", 100) < 50:
                                warnings.append(
                                    f"{sample}: CpG coverage rate only "
                                    f"{bed['coverage_rate_pct']:.1f}%")
                        else:
                            warnings.append(f"{sample}: pileup parse error — {bed['error']}")

                # ── DMR (DSS) → DMR bar + effect size ────────────────────────
                dss_dir = os.path.join(sample_path, "dmr_haplotype_level", "dss")
                if os.path.isdir(dss_dir):
                    dmr_files = [f for f in os.listdir(dss_dir)
                                 if f.endswith("_callDMR.txt")]
                    if dmr_files:
                        dmrs = _parse_dss_dmr(os.path.join(dss_dir, dmr_files[0]))
                        if dmrs:
                            s["dmr"] = {
                                "total_dmrs": len(dmrs),
                                "mean_diff":  round(
                                    float(np.mean([abs(d["diff"]) for d in dmrs])), 4),
                            }
                            plot_paths.extend(_plot_dmr(
                                dmrs, sample, os.path.join(analysis_dir, "dmr")))
                        else:
                            warnings.append(f"{sample}: callDMR.txt found but no DMRs parsed")

                # ── Haplotype comparison → scatter + violin ───────────────────
                modkit_dir = os.path.join(sample_path, "dmr_haplotype_level", "modkit")
                if os.path.isdir(modkit_dir):
                    h1, h2 = _parse_hap_beds(modkit_dir)
                    if h1.size > 0:
                        s["haplotype"] = {
                            "common_sites": int(h1.size),
                            "mean_hap1":    round(float(h1.mean()), 4),
                            "mean_hap2":    round(float(h2.mean()), 4),
                        }
                        plot_paths.extend(_plot_haplotype(
                            h1, h2, sample, os.path.join(analysis_dir, "haplotype")))
                    else:
                        warnings.append(f"{sample}: haplotype bed files not found in modkit dir")

                # ── phase read counts ─────────────────────────────────────────
                phase_dir = os.path.join(sample_path, "phase")
                if os.path.isdir(phase_dir):
                    readlists = [f for f in os.listdir(phase_dir) if f.endswith(".readlist")]
                    if readlists:
                        s["phasing"] = {"readlist_files": len(readlists)}

                if s:
                    per_sample[sample] = s

        summary["per_sample"] = per_sample
        return {
            "workflow":   "methylong",
            "summary":    summary,
            "plot_paths": plot_paths,
            "warnings":   warnings,
        }
