"""
BAM 分析可视化模块。
根据 BamAnalyzer 返回的 stats dict 生成 PNG 图表，保存到指定目录。

生成图表：
  1. mapping_stats.png  — 比对情况饼图（mapped / unmapped / secondary / supplementary）
  2. read_length.png    — read 长度分布直方图（来自 samtools stats RL 行）
  3. quality_dist.png   — 碱基质量分布柱状图（来自 samtools stats QUAL 行）
  4. bam_summary.png    — 以上三图合并的总览图（同时返回）

返回已生成的文件路径列表。
"""
import os

# matplotlib 在无显示器环境下必须使用非交互后端
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ── 调色板 ────────────────────────────────────────────────────────────────────
_PALETTE = {
    "mapped":        "#4C9BE8",
    "unmapped":      "#E87B4C",
    "secondary":     "#A8D5A2",
    "supplementary": "#C9B1E8",
    "background":    "#F8F9FA",
    "grid":          "#E0E0E0",
    "text":          "#2C3E50",
}

_FONT = {"family": "DejaVu Sans", "size": 11}
plt.rcParams.update({
    "font.family":       _FONT["family"],
    "font.size":         _FONT["size"],
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "axes.facecolor":    _PALETTE["background"],
    "figure.facecolor":  "white",
    "axes.grid":         True,
    "grid.color":        _PALETTE["grid"],
    "grid.linewidth":    0.8,
})


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _save(fig: plt.Figure, path: str) -> str:
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _fmt_num(n: int) -> str:
    """将大数字格式化为 1.23M / 456K 形式。"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ── 图1：比对情况饼图 ─────────────────────────────────────────────────────────

def plot_mapping_stats(stats: dict, output_dir: str) -> str:
    total      = stats.get("total_reads", 0)
    mapped     = stats.get("primary_mapped", stats.get("mapped_reads", 0))
    secondary  = stats.get("secondary", 0)
    suppl      = stats.get("supplementary", 0)
    unmapped   = max(0, total - mapped - secondary - suppl)
    mapped_rate = stats.get("mapped_rate", 0.0)

    labels  = ["Primary Mapped", "Unmapped", "Secondary", "Supplementary"]
    values  = [mapped, unmapped, secondary, suppl]
    colors  = [_PALETTE["mapped"], _PALETTE["unmapped"],
               _PALETTE["secondary"], _PALETTE["supplementary"]]

    # 过滤掉 0 值
    data = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not data:
        return ""

    labels_f, values_f, colors_f = zip(*data)

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        values_f,
        labels=None,
        colors=colors_f,
        autopct=lambda p: f"{p:.1f}%" if p > 1 else "",
        startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_color("white")
        at.set_fontweight("bold")

    # 图例
    legend_labels = [f"{l}  ({_fmt_num(v)})" for l, v in zip(labels_f, values_f)]
    ax.legend(wedges, legend_labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=2, fontsize=9)

    ax.set_title(
        f"Mapping Statistics\nTotal: {_fmt_num(total)}  |  Mapped Rate: {mapped_rate:.1f}%",
        pad=12, color=_PALETTE["text"],
    )
    fig.patch.set_facecolor("white")

    path = os.path.join(output_dir, "mapping_stats.png")
    return _save(fig, path)


# ── 图2：Read 长度分布 ────────────────────────────────────────────────────────

def plot_read_length(stats: dict, output_dir: str) -> str:
    rl_dist: dict = stats.get("read_length_dist", {})
    if not rl_dist:
        return ""

    lengths = sorted(rl_dist.keys())
    counts  = [rl_dist[l] for l in lengths]
    avg_len = stats.get("avg_read_length", 0)

    # 若数据点过多则分桶（>200 个不同长度时合并）
    if len(lengths) > 200:
        arr  = np.array(lengths)
        wt   = np.array(counts)
        bins = np.linspace(arr.min(), arr.max(), 101)
        hist, edges = np.histogram(arr, bins=bins, weights=wt)
        x     = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]
    else:
        x     = np.array(lengths, dtype=float)
        hist  = np.array(counts, dtype=float)
        width = max(1.0, (x[-1] - x[0]) / max(len(x) - 1, 1))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x, hist, width=width * 0.9, color=_PALETTE["mapped"],
           alpha=0.85, edgecolor="white", linewidth=0.4)

    if avg_len:
        ax.axvline(avg_len, color=_PALETTE["unmapped"], linestyle="--",
                   linewidth=1.5, label=f"Mean: {avg_len:.0f} bp")
        ax.legend(fontsize=9)

    ax.set_xlabel("Read Length (bp)", color=_PALETTE["text"])
    ax.set_ylabel("Read Count",       color=_PALETTE["text"])
    ax.set_title("Read Length Distribution", color=_PALETTE["text"])
    ax.tick_params(colors=_PALETTE["text"])
    fig.tight_layout()

    path = os.path.join(output_dir, "read_length.png")
    return _save(fig, path)


# ── 图3：碱基质量分布 ─────────────────────────────────────────────────────────

def plot_quality_dist(stats: dict, output_dir: str) -> str:
    qual_dist: dict = stats.get("quality_dist", {})
    if not qual_dist:
        return ""

    scores = sorted(qual_dist.keys())
    counts = [qual_dist[s] for s in scores]
    avg_q  = stats.get("avg_quality", None)
    total  = sum(counts) or 1

    # 颜色按 Q 值分段
    def _color(q: int) -> str:
        if q >= 20: return _PALETTE["mapped"]
        if q >= 10: return "#F5A623"
        return _PALETTE["unmapped"]

    colors = [_color(s) for s in scores]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(scores, [c / total * 100 for c in counts],
                  color=colors, alpha=0.9, edgecolor="white", linewidth=0.3)

    if avg_q is not None:
        ax.axvline(avg_q, color=_PALETTE["text"], linestyle="--",
                   linewidth=1.5, label=f"Mean Q: {avg_q:.1f}")
        ax.legend(fontsize=9)

    # 图例色块
    patches = [
        mpatches.Patch(color=_PALETTE["mapped"],   label="Q≥20 (High)"),
        mpatches.Patch(color="#F5A623",            label="Q10-19 (Medium)"),
        mpatches.Patch(color=_PALETTE["unmapped"], label="Q<10 (Low)"),
    ]
    ax.legend(handles=patches, fontsize=8, loc="upper left")

    ax.set_xlabel("Base Quality Score (Phred)", color=_PALETTE["text"])
    ax.set_ylabel("Fraction (%)",               color=_PALETTE["text"])
    ax.set_title("Base Quality Distribution",   color=_PALETTE["text"])
    ax.tick_params(colors=_PALETTE["text"])
    fig.tight_layout()

    path = os.path.join(output_dir, "quality_dist.png")
    return _save(fig, path)


# ── 汇总图（3合1）────────────────────────────────────────────────────────────

def plot_bam_summary(stats: dict, output_dir: str) -> str:
    """
    将三张图合并为一张 3-panel 总览图。
    若某个子图数据缺失则跳过该 panel。
    """
    has_mapping = stats.get("total_reads", 0) > 0
    has_rl      = bool(stats.get("read_length_dist"))
    has_qual    = bool(stats.get("quality_dist"))

    panels = sum([has_mapping, has_rl, has_qual])
    if panels == 0:
        return ""

    fig, axes = plt.subplots(1, panels, figsize=(6 * panels, 4.5))
    if panels == 1:
        axes = [axes]

    ax_idx = 0

    # ── Mapping pie ──────────────────────────────────────────────────────────
    if has_mapping:
        ax = axes[ax_idx]; ax_idx += 1
        total       = stats.get("total_reads", 0)
        mapped      = stats.get("primary_mapped", stats.get("mapped_reads", 0))
        secondary   = stats.get("secondary", 0)
        suppl       = stats.get("supplementary", 0)
        unmapped    = max(0, total - mapped - secondary - suppl)
        mapped_rate = stats.get("mapped_rate", 0.0)

        data = [(v, l, c) for v, l, c in [
            (mapped,    "Mapped",        _PALETTE["mapped"]),
            (unmapped,  "Unmapped",      _PALETTE["unmapped"]),
            (secondary, "Secondary",     _PALETTE["secondary"]),
            (suppl,     "Supplementary", _PALETTE["supplementary"]),
        ] if v > 0]

        values_f, labels_f, colors_f = zip(*data)
        wedges, _, autotexts = ax.pie(
            values_f, colors=colors_f, startangle=90,
            autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
            wedgeprops={"edgecolor": "white", "linewidth": 1.2},
        )
        for at in autotexts:
            at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
        legend_lbs = [f"{l} ({_fmt_num(v)})" for l, v in zip(labels_f, values_f)]
        ax.legend(wedges, legend_lbs, loc="lower center",
                  bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=8)
        ax.set_title(f"Mapping Stats\n{_fmt_num(total)} reads | {mapped_rate:.1f}% mapped",
                     fontsize=11, color=_PALETTE["text"])

    # ── Read length hist ─────────────────────────────────────────────────────
    if has_rl:
        ax = axes[ax_idx]; ax_idx += 1
        rl_dist  = stats["read_length_dist"]
        lengths  = sorted(rl_dist.keys())
        counts   = [rl_dist[l] for l in lengths]
        avg_len  = stats.get("avg_read_length", 0)

        if len(lengths) > 200:
            arr  = np.array(lengths); wt = np.array(counts)
            bins = np.linspace(arr.min(), arr.max(), 81)
            hist, edges = np.histogram(arr, bins=bins, weights=wt)
            x     = (edges[:-1] + edges[1:]) / 2
            width = edges[1] - edges[0]
        else:
            x     = np.array(lengths, dtype=float)
            hist  = np.array(counts,  dtype=float)
            width = max(1.0, (x[-1] - x[0]) / max(len(x) - 1, 1))

        ax.bar(x, hist, width=width * 0.9,
               color=_PALETTE["mapped"], alpha=0.85,
               edgecolor="white", linewidth=0.3)
        if avg_len:
            ax.axvline(avg_len, color=_PALETTE["unmapped"], linestyle="--",
                       linewidth=1.5, label=f"Mean {avg_len:.0f} bp")
            ax.legend(fontsize=8)
        ax.set_xlabel("Read Length (bp)", fontsize=10)
        ax.set_ylabel("Count",            fontsize=10)
        ax.set_title("Read Length Distribution", fontsize=11, color=_PALETTE["text"])

    # ── Quality dist bar ─────────────────────────────────────────────────────
    if has_qual:
        ax = axes[ax_idx]; ax_idx += 1
        qual_dist = stats["quality_dist"]
        scores    = sorted(qual_dist.keys())
        counts    = [qual_dist[s] for s in scores]
        avg_q     = stats.get("avg_quality")
        total_q   = sum(counts) or 1

        colors = [(_PALETTE["mapped"] if s >= 20
                   else "#F5A623" if s >= 10
                   else _PALETTE["unmapped"]) for s in scores]

        ax.bar(scores, [c / total_q * 100 for c in counts],
               color=colors, alpha=0.9, edgecolor="white", linewidth=0.3)
        if avg_q is not None:
            ax.axvline(avg_q, color=_PALETTE["text"], linestyle="--",
                       linewidth=1.5, label=f"Mean Q{avg_q:.1f}")
            ax.legend(fontsize=8)
        patches = [
            mpatches.Patch(color=_PALETTE["mapped"],   label="Q≥20"),
            mpatches.Patch(color="#F5A623",            label="Q10-19"),
            mpatches.Patch(color=_PALETTE["unmapped"], label="Q<10"),
        ]
        ax.legend(handles=patches, fontsize=7, loc="upper left")
        ax.set_xlabel("Phred Score", fontsize=10)
        ax.set_ylabel("Fraction (%)", fontsize=10)
        ax.set_title("Base Quality Distribution", fontsize=11, color=_PALETTE["text"])

    fig.suptitle(f"BAM QC Summary — {stats.get('file', '')}", fontsize=13,
                 color=_PALETTE["text"], y=1.02)
    fig.tight_layout()

    path = os.path.join(output_dir, "bam_summary.png")
    return _save(fig, path)


# ── 主入口 ────────────────────────────────────────────────────────────────────

def generate_bam_plots(stats: dict, output_dir: str) -> list[str]:
    """
    生成所有 BAM 图表，返回已成功写入的文件路径列表。
    单张图 + 合并总览图都会生成。
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    try:
        p = plot_bam_summary(stats, output_dir)
        if p:
            paths.append(p)
    except Exception as e:
        print(f"[BamPlotter] bam_summary 生成失败: {e}")

    for fn, plotter in [
        ("mapping_stats.png", plot_mapping_stats),
        ("read_length.png",   plot_read_length),
        ("quality_dist.png",  plot_quality_dist),
    ]:
        try:
            p = plotter(stats, output_dir)
            if p and p not in paths:
                paths.append(p)
        except Exception as e:
            print(f"[BamPlotter] {fn} 生成失败: {e}")

    return paths
