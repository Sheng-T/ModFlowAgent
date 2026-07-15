"""Profile-driven builder for pacbio_dna local workflows."""
from __future__ import annotations

import os
import string

from configs.runtime_config import TOOL_THREADS
from tools.workflow.caller_profiles import get_modcaller_profile
from tools.workflow.local.profile_common import (
    _SafeFormatDict,
    build_pbmm2_align_command,
    get_known_outputs,
    render_command_template,
    resolve_input_bam,
    skip_if_exists,
)
from tools.toolchain.modkit.validator import get_modkit_flags


def build_step_command(
    step: str,
    prereq: dict,
    data_path: dict,
    step_dir: str,
    all_step_dirs: dict,
) -> "tuple[str, str] | None":
    _ = data_path
    data_file = prereq.get("data_file", "") or ""
    reference = prereq.get("reference", "") or ""
    mod_type = (prereq.get("modification_type") or "5mcpg").strip()
    modcaller = prereq.get("modcaller", "") or prereq.get("caller", "")
    profile = get_modcaller_profile("pacbio_dna", modcaller) if modcaller else {}
    caller_steps = list(profile.get("caller_steps", []))
    known = get_known_outputs(all_step_dirs, data_file=data_file, reference=reference, step_dir=step_dir)

    if not modcaller:
        return ("workflow", "error: pacbio_dna has no configured modcaller profile yet")

    if step == "modcaller_run":
        return render_command_template("pacbio_dna", prereq, step_dir, all_step_dirs, data_path)

    if step == "pbmm2_align":
        modcaller_before_align = False
        if "modcaller_run" in caller_steps and "pbmm2_align" in caller_steps:
            modcaller_before_align = caller_steps.index("modcaller_run") < caller_steps.index("pbmm2_align")
        return build_pbmm2_align_command(
            prereq,
            step_dir,
            all_step_dirs,
            prefer_modcaller=modcaller_before_align,
        )

    if step == "samtools_sort":
        in_bam = resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=False)
        if not in_bam:
            return ("workflow", "error: samtools_sort could not resolve an input BAM")
        out_bam = os.path.join(step_dir, "sorted.bam")
        raw = f'samtools sort -@{TOOL_THREADS} "{in_bam}" -o "{out_bam}"'
        return ("samtools", skip_if_exists(out_bam, raw))

    if step == "samtools_index":
        input_bam = (
            known["sorted_bam"]
            or known["aligned_bam"]
            or known["modcaller_bam"]
            or resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=True)
        )
        if not input_bam:
            return ("workflow", "error: samtools_index could not resolve an input BAM")
        bai = input_bam + ".bai"
        raw = f'samtools index -@{TOOL_THREADS} "{input_bam}"'
        return ("samtools", skip_if_exists(bai, raw))

    if step == "samtools_faidx":
        if not reference:
            return None
        local_ref = os.path.join(step_dir, os.path.basename(reference))
        local_fai = local_ref + ".fai"
        raw = f'ln -sf "{reference}" "{local_ref}" && samtools faidx "{local_ref}"'
        return ("samtools", skip_if_exists(local_fai, raw))

    if step == "pb_cpg_tools_run":
        if not reference or mod_type != "5mcpg":
            return None
        input_bam = known["aligned_bam"] or resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=False)
        if not input_bam:
            return ("workflow", "error: pb_cpg_tools_run could not resolve an aligned BAM")
        prefix = os.path.join(step_dir, "pbcpg")
        positive_bed = os.path.join(step_dir, "pbcpg_positive.bed.gz")
        negative_bed = os.path.join(step_dir, "pbcpg_negative.bed.gz")
        combined_bed = os.path.join(step_dir, "pbcpg.combined.bed.gz")
        faidx_dir = all_step_dirs.get("samtools_faidx", "")
        local_ref = os.path.join(faidx_dir, os.path.basename(reference)) if faidx_dir else reference
        raw = (
            f'aligned_bam_to_cpg_scores '
            f'--bam "{input_bam}" '
            f'--output-prefix "{prefix}" '
            f'--threads {TOOL_THREADS} '
            f'--ref "{local_ref}" '
            f'--modsites-mode reference '
            f'--pileup-mode model && '
            f'if [ -f "{prefix}.hap1.bed.gz" ] && [ -f "{prefix}.hap2.bed.gz" ]; then '
            f'mv "{prefix}.hap1.bed.gz" "{positive_bed}" && '
            f'mv "{prefix}.hap2.bed.gz" "{negative_bed}"; '
            f'elif [ -f "{combined_bed}" ]; then '
            f'cp "{combined_bed}" "{positive_bed}"; '
            f'else '
            f'echo "pb-CpG-tools produced neither hap1/hap2 nor combined bed output" >&2; exit 1; '
            f'fi'
        )
        return ("pb-cpg-tools", skip_if_exists(positive_bed, raw))

    if step == "ccsmeth_callfreqb_run":
        if not reference or mod_type != "5mcpg":
            return None
        input_bam = known["aligned_bam"] or resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=False)
        if not input_bam:
            return ("workflow", "error: ccsmeth_callfreqb_run could not resolve an aligned BAM")
        faidx_dir = all_step_dirs.get("samtools_faidx", "")
        local_ref = os.path.join(faidx_dir, os.path.basename(reference)) if faidx_dir else reference
        raw_dir = os.path.join(step_dir, "ccsmeth_freqb_raw")
        out_prefix = os.path.join(raw_dir, "ccsmeth_freqb")
        out_bed = os.path.join(step_dir, "ccsmeth_freqb.bed.gz")
        model_template = profile.get("template_vars", {}).get("ccsmeth_ag_model", "")
        model = string.Formatter().vformat(
            model_template,
            (),
            _SafeFormatDict({
                "pipeline_dir": data_path.get("pipeline_dir", ""),
                "base_data_dir": data_path.get("base_data_dir", ""),
                "step_dir": step_dir,
                "run_dir": os.path.dirname(step_dir),
            }),
        ) if model_template else ""
        raw = (
            f'mkdir -p "{raw_dir}" && '
            f'{profile.get("entrypoint", "ccsmeth")} call_freqb '
            f'--sort --bed --gzip --call_mode aggregate '
            f'--input_bam "{input_bam}" '
            f'--ref "{local_ref}" '
            f'--aggre_model "{model}" '
            f'--output "{out_prefix}" '
            f'--threads {TOOL_THREADS} && '
            f'first_bed=$(find "{raw_dir}" -maxdepth 1 -type f -name "*.bed.gz" | head -n 1) && '
            f'[ -n "$first_bed" ] && cp "$first_bed" "{out_bed}"'
        )
        return ("ccsmeth", skip_if_exists(out_bed, raw))

    if step == "modkit_pileup":
        if not reference or mod_type == "none":
            return None
        input_bam = known["sorted_bam"] or resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=False)
        if not input_bam:
            return ("workflow", "error: modkit_pileup could not resolve an input BAM")
        out_bed = os.path.join(step_dir, "pileup.bed")
        flags = get_modkit_flags("DNA", mod_type)
        extra = flags["pileup_extra"]
        faidx_dir = all_step_dirs.get("samtools_faidx", "")
        local_ref = os.path.join(faidx_dir, os.path.basename(reference)) if faidx_dir else reference
        bind_hint = f': "{reference}"; ' if local_ref != reference else ""
        parts = (f'{bind_hint}modkit pileup "{input_bam}" "{out_bed}" --ref "{local_ref}"'
                 f' -t {TOOL_THREADS} --no-filtering')
        if extra:
            parts += f" {extra}"
        return ("modkit", skip_if_exists(out_bed, parts))

    if step == "modkit_extract":
        if mod_type == "none":
            return None
        input_bam = known["sorted_bam"] or resolve_input_bam(all_step_dirs, data_file=data_file, prefer_modcaller=False)
        if not input_bam:
            return ("workflow", "error: modkit_extract could not resolve an input BAM")
        out_tsv = os.path.join(step_dir, "extract.tsv")
        flags = get_modkit_flags("DNA", mod_type)
        extra = flags["extract_extra"]
        faidx_dir = all_step_dirs.get("samtools_faidx", "")
        local_ref = os.path.join(faidx_dir, os.path.basename(reference)) if (reference and faidx_dir) else reference
        bind_hint = f': "{reference}"; ' if (local_ref and local_ref != reference) else ""
        ref_arg = f' --ref "{local_ref}"' if local_ref else ""
        parts = f'{bind_hint}modkit extract full "{input_bam}" "{out_tsv}"{ref_arg} -t {TOOL_THREADS}'
        if extra:
            parts += f" {extra}"
        return ("modkit", skip_if_exists(out_tsv, parts))

    return ("workflow", f"error: pacbio_dna step '{step}' is not implemented")
