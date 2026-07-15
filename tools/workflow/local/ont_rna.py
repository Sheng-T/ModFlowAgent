"""
Deterministic step builder for the ont_rna local workflow.

Handles any ONT direct-RNA modification type (m6A, pseU, inosine, all, …)
by resolving the correct dorado model pair from tools/workflow/model_map.py.

Steps:
  dorado_download     — download basecall + mod model (skip if already present)
  dorado_basecaller   — basecall with modification detection
  samtools_sort       — coordinate-sort BAM
  samtools_index      — index sorted BAM
  samtools_faidx      — index reference FASTA (only when reference provided)
  modkit_pileup       — site-level bedMethyl  (only when reference provided)
  modkit_extract      — per-read modification table (always)

Fixed output filenames (no timestamps):
  calls.bam  /  sorted.bam  /  pileup.bed  /  extract.tsv

Resume logic: if a step's expected output already exists, the command is wrapped
with a [ -f output ] || ... guard so the step is skipped automatically.
"""
import os

from configs.runtime_config import TOOL_THREADS
from tools.workflow.local.profile_common import render_command_template, skip_if_exists
from tools.toolchain.dorado.validator import resolve_models
from tools.toolchain.modkit.validator import get_modkit_flags
from utils.runner_utils import find_all_free_gpus


def build_step_command(
    step: str,
    prereq: dict,
    data_path: dict,
    step_dir: str,
    all_step_dirs: dict,
) -> "tuple[str, str] | None":
    data_file  = prereq.get("data_file", "")
    reference  = prereq.get("reference", "")
    mod_type   = (prereq.get("modification_type") or "m6a").strip()
    device     = (prereq.get("device") or "cpu").strip() or "cpu"
    modcaller  = (prereq.get("modcaller") or prereq.get("caller") or "dorado").strip().lower()
    model_dir  = data_path.get("dorado_models", "")
    use_dorado_mod_model = modcaller == "dorado"

    basecall_model, mod_model = resolve_models("RNA", mod_type)
    basecall_path = os.path.join(model_dir, basecall_model)

    if step == "dorado_download":
        dl_base = (
            f'([ -d "{basecall_path}" ] || '
            f'dorado download --model {basecall_model} --directory "{model_dir}")'
        )
        if mod_model and use_dorado_mod_model:
            mod_model_path = os.path.join(model_dir, mod_model)
            dl_mod = (
                f'([ -d "{mod_model_path}" ] || '
                f'dorado download --model {mod_model} --directory "{model_dir}")'
            )
            return ("dorado", f"{dl_base} && {dl_mod}")
        return ("dorado", dl_base)

    if step == "dorado_basecaller":
        out_bam = os.path.join(step_dir, "calls.bam")

        cmd_parts = [f'dorado basecaller "{basecall_path}" "{data_file}"']
        if mod_model and use_dorado_mod_model:
            mod_model_path = os.path.join(model_dir, mod_model)
            cmd_parts.append(f'--modified-bases-models "{mod_model_path}"')
        cmd_parts.append("--emit-moves")

        resolved_device = device
        if resolved_device == "auto":
            gpu_list = find_all_free_gpus(min_free_mb=10000)
            resolved_device = gpu_list if gpu_list else "cpu"
        cmd_parts.append(f"--device {resolved_device}")

        if reference:
            cmd_parts.append(f'--reference "{reference}"')

        cmd_parts.append(f'> "{out_bam}"')
        raw = " ".join(cmd_parts)
        return ("dorado", skip_if_exists(out_bam, raw))

    if step == "samtools_sort":
        in_bam  = os.path.join(all_step_dirs.get("dorado_basecaller", ""), "calls.bam")
        out_bam = os.path.join(step_dir, "sorted.bam")
        raw = f'samtools sort -@{TOOL_THREADS} "{in_bam}" -o "{out_bam}"'
        return ("samtools", skip_if_exists(out_bam, raw))

    if step == "samtools_index":
        sorted_bam = os.path.join(all_step_dirs.get("samtools_sort", ""), "sorted.bam")
        bai = sorted_bam + ".bai"
        raw = f'samtools index -@{TOOL_THREADS} "{sorted_bam}"'
        return ("samtools", skip_if_exists(bai, raw))

    if step == "samtools_faidx":
        if not reference:
            return None
        # Write .fai into step_dir via a symlink to avoid permission issues
        # with read-only reference directories.
        local_ref = os.path.join(step_dir, os.path.basename(reference))
        local_fai = local_ref + ".fai"
        raw = f'ln -sf "{reference}" "{local_ref}" && samtools faidx "{local_ref}"'
        return ("samtools", skip_if_exists(local_fai, raw))

    if step == "modkit_pileup":
        if not reference or mod_type == "none":
            return None
        sorted_bam = os.path.join(all_step_dirs.get("samtools_sort", ""), "sorted.bam")
        out_bed    = os.path.join(step_dir, "pileup.bed")
        flags      = get_modkit_flags("RNA", mod_type)
        extra      = flags["pileup_extra"]
        faidx_dir  = all_step_dirs.get("samtools_faidx", "")
        local_ref  = os.path.join(faidx_dir, os.path.basename(reference)) if faidx_dir else reference
        bind_hint  = f': "{reference}"; ' if local_ref != reference else ""
        parts = (f'{bind_hint}modkit pileup "{sorted_bam}" "{out_bed}" --ref "{local_ref}"'
                 f' -t {TOOL_THREADS} --no-filtering')
        if extra:
            parts += f" {extra}"
        return ("modkit", skip_if_exists(out_bed, parts))

    if step == "modkit_extract":
        if mod_type == "none":
            return None
        sorted_bam = os.path.join(all_step_dirs.get("samtools_sort", ""), "sorted.bam")
        out_tsv    = os.path.join(step_dir, "extract.tsv")
        flags      = get_modkit_flags("RNA", mod_type)
        extra      = flags["extract_extra"]
        faidx_dir  = all_step_dirs.get("samtools_faidx", "")
        local_ref  = os.path.join(faidx_dir, os.path.basename(reference)) if (reference and faidx_dir) else reference
        bind_hint  = f': "{reference}"; ' if (local_ref and local_ref != reference) else ""
        ref_arg    = f' --ref "{local_ref}"' if local_ref else ""
        parts = f'{bind_hint}modkit extract full "{sorted_bam}" "{out_tsv}"{ref_arg} -t {TOOL_THREADS}'
        if extra:
            parts += f" {extra}"
        return ("modkit", skip_if_exists(out_tsv, parts))

    if step == "modcaller_run":
        return render_command_template("ont_rna", prereq, step_dir, all_step_dirs, data_path)

    return None
