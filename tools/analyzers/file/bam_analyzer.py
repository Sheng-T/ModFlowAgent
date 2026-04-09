"""
BAM 文件统计分析器。
通过 Singularity 容器调用 samtools flagstat / samtools stats 获取统计信息。
"""
import os
import re
import subprocess

from configs.path_config import IMAGE_PATH
from tools.analyzers.file.base import FileAnalyzer


def _resolve_samtools_image() -> str | None:
    """扫描 {image_store}/samtools/ 目录，优先返回 .img，其次 .sif。"""
    tool_dir = os.path.join(os.path.expanduser(IMAGE_PATH["image_store"]), "samtools")
    if not os.path.isdir(tool_dir):
        return None
    img_files = [f for f in os.listdir(tool_dir) if f.endswith((".img", ".sif"))]
    if not img_files:
        return None
    img_files.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
    return os.path.join(tool_dir, img_files[0])


def _build_singularity_cmd(bam_path: str, samtools_args: str) -> str:
    image_path = _resolve_samtools_image()
    bam_dir    = os.path.dirname(os.path.abspath(bam_path))
    if image_path:
        return (
            f"singularity exec "
            f"--bind {bam_dir}:{bam_dir} "
            f"{image_path} "
            f"samtools {samtools_args}"
        )
    # 未找到镜像，回退到本地 samtools
    print("[BamAnalyzer] 未找到 samtools 镜像，尝试本地执行")
    return f"samtools {samtools_args}"


def _run(cmd: str, timeout: int = 120) -> tuple[str, str]:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr


def _parse_flagstat(text: str) -> dict:
    """
    解析 samtools flagstat 输出。
    示例行：1234567 + 0 mapped (99.50% : N/A)
    """
    stats = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 提取第一个数字（QC-passed reads 计数）
        m_count = re.match(r'^(\d+)\s*\+\s*\d+\s+(.+)', line)
        if not m_count:
            continue
        count = int(m_count.group(1))
        desc  = m_count.group(2).lower()

        if "in total" in desc:
            stats["total_reads"] = count
        elif "primary" in desc and "mapped" in desc and "duplicate" not in desc:
            stats["primary_mapped"] = count
        elif "mapped" in desc and "primary" not in desc and "duplicate" not in desc:
            stats["mapped_reads"] = count
        elif "secondary" in desc:
            stats["secondary"] = count
        elif "supplementary" in desc:
            stats["supplementary"] = count

    # 映射率（从 "mapped (X.XX%...)" 中提取）
    m_rate = re.search(r'mapped\s*\(([0-9.]+)%', text)
    if m_rate:
        stats["mapped_rate"] = round(float(m_rate.group(1)), 2)
    return stats


def _parse_stats(text: str) -> dict:
    """
    从 samtools stats 输出提取：
      - SN 行：avg_quality / avg_read_length / reads_examined
      - RL 行：read_length_dist  {length: count}
      - QUAL 行：quality_dist {score: count}（每 cycle 质量行，累加得总分布）
    """
    stats: dict = {}
    rl_dist: dict[int, int]   = {}
    qual_dist: dict[int, int] = {}

    for line in text.splitlines():
        if line.startswith("SN"):
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            key = parts[1].strip().rstrip(":")
            val = parts[2].strip()
            if key == "average quality":
                try:
                    stats["avg_quality"] = round(float(val), 2)
                except ValueError:
                    pass
            elif key == "average length":
                try:
                    stats["avg_read_length"] = round(float(val), 1)
                except ValueError:
                    pass
            elif key == "reads examined":
                try:
                    stats["reads_examined"] = int(val)
                except ValueError:
                    pass

        elif line.startswith("RL\t"):
            # RL  <length>  <count>
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    rl_dist[int(parts[1])] = int(parts[2])
                except ValueError:
                    pass

        elif line.startswith("QUAL\t"):
            # QUAL  <cycle>  <q0_count>  <q1_count> ... <q40_count>
            # 累加各 quality bucket 的 count
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            for q_idx, cnt_str in enumerate(parts[2:], start=0):
                try:
                    cnt = int(cnt_str)
                    if cnt > 0:
                        qual_dist[q_idx] = qual_dist.get(q_idx, 0) + cnt
                except ValueError:
                    pass

    if rl_dist:
        stats["read_length_dist"] = rl_dist
    if qual_dist:
        stats["quality_dist"] = qual_dist
    return stats


class BamAnalyzer(FileAnalyzer):
    def analyze(self, file_path: str) -> dict:
        if not os.path.isfile(file_path):
            return {"error": f"文件不存在: {file_path}"}

        result = {"file": os.path.basename(file_path), "type": "bam"}

        try:
            # 1. flagstat
            cmd_flag = _build_singularity_cmd(file_path, f"flagstat {file_path}")
            out_flag, err_flag = _run(cmd_flag)
            if out_flag:
                result.update(_parse_flagstat(out_flag))
            else:
                result["flagstat_error"] = err_flag[:200]
        except Exception as e:
            result["flagstat_error"] = str(e)

        try:
            # 2. stats（只取 SN 部分，速度快）
            cmd_stats = _build_singularity_cmd(file_path, f"stats {file_path}")
            out_stats, err_stats = _run(cmd_stats, timeout=180)
            if out_stats:
                result.update(_parse_stats(out_stats))
            else:
                result["stats_error"] = err_stats[:200]
        except Exception as e:
            result["stats_error"] = str(e)

        return result
