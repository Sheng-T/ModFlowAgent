"""
methylong workflow validators.

Two concerns handled here:
1. methylong()  — runtime command builder validator (called by WORKFLOW_REGISTRY)
2. validate_samplesheet() / fix_paths() — pre-run samplesheet checks (called by prereq node)
"""
import copy
import csv
import io
import os

from configs.workflow_config import pipeline_exists
from tools.workflow.command_builder import build_workflow_command


# ── Runtime command builder validator ─────────────────────────────────────────

def validate_nfcore_kwargs(kwargs: dict) -> str | None:
    pipeline = kwargs.get("pipeline", "")
    if not pipeline:
        return "Error: nextflow nf-core requires kwargs['pipeline']."
    if not pipeline_exists(pipeline):
        return (
            "Error: unsupported nf-core pipeline. Supported pipelines: "
            "methylong, rnaseq, sarek, ampliseq, methylseq, mag, taxprofiler."
        )
    if not kwargs.get("input"):
        return "Error: nextflow nf-core requires kwargs['input'] (samplesheet)."
    if not kwargs.get("outdir"):
        return "Error: nextflow nf-core requires kwargs['outdir']."
    return None


def methylong(args_dict, data_path):
    """
    Verify and build nf-core/nextflow command.
    Called by WORKFLOW_REGISTRY with (tool_args, data_path).
    """
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    err = validate_nfcore_kwargs(kwargs)
    if err:
        return err
    return build_workflow_command(kwargs, data_path)


# ── Samplesheet validation (called by prereq node after LLM generation) ───────

_REF_EXTENSIONS = {".fa", ".fasta", ".fna"}


def _bam_has_mod_tags(path: str, max_reads: int = 100) -> bool:
    """Return True if the BAM contains MM/ML base modification tags."""
    try:
        import pysam  # type: ignore[import]
        with pysam.AlignmentFile(path, "rb", check_sq=False) as bam:
            checked = 0
            for read in bam.fetch(until_eof=True):
                if read.is_unmapped:
                    continue
                tags = {t[0] for t in (read.tags or [])}
                if "MM" in tags and "ML" in tags:
                    return True
                checked += 1
                if checked >= max_reads:
                    break
        return False
    except ImportError:
        pass
    except Exception:
        return True  # can't check → assume OK

    try:
        import subprocess
        result = subprocess.run(
            ["samtools", "view", path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return True  # samtools unavailable → assume OK
        for line in result.stdout.splitlines()[:max_reads]:
            if "\tMM:" in line and "\tML:" in line:
                return True
        return False
    except Exception:
        return True  # can't check → assume OK

_DMR_KEYWORDS = {
    "dmr", "differential methylation", "population-scale", "population scale",
    "group comparison", "between groups", "compare groups", "dmr analysis",
    "差异甲基化", "群体分析", "组间比较", "组间差异", "样本组比较",
}
_HAPLOTYPE_KEYWORDS = {
    "haplotype", "haplotype-level", "allele-specific", "allele specific", "ase", "phased",
    "单倍型", "等位基因特异", "相位",
}


def fix_paths(content: str, uploaded_files: list[str]) -> str:
    """Fix wrong-directory paths and auto-fill empty ref from uploaded files."""
    if not uploaded_files:
        return content
    basename_map = {os.path.basename(f): f for f in uploaded_files}
    ref_candidates = [f for f in uploaded_files
                      if os.path.splitext(f)[1].lower() in _REF_EXTENSIONS]
    try:
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    except Exception:
        return content

    changed = False
    for row in rows:
        for col in ("path", "ref"):
            val = (row.get(col) or "").strip()
            if not val or os.path.isfile(val) or os.path.isdir(val):
                continue
            basename = os.path.basename(val)
            if basename in basename_map:
                print(f"[MethylongValidator] Path corrected: {val!r} → {basename_map[basename]!r}")
                row[col] = basename_map[basename]
                changed = True
        if "ref" in fieldnames and not (row.get("ref") or "").strip() and ref_candidates:
            row["ref"] = ref_candidates[0]
            print(f"[MethylongValidator] ref auto-filled: {ref_candidates[0]!r}")
            changed = True

    if not changed:
        return content
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def validate_samplesheet(content: str, user_input: str) -> list[dict]:
    """
    Validate the generated samplesheet for common biological/data errors.
    Returns list of {"level": "error"|"warning", "message": str}.
    """
    issues: list[dict] = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception:
        return issues

    # 1. Missing files / directories
    for i, row in enumerate(rows, 1):
        method = (row.get("method") or "").strip().lower()
        # ref is required for methylong
        if not (row.get("ref") or "").strip():
            issues.append({
                "level": "error",
                "message": (
                    f"Row {i}: `ref` (reference genome FASTA) is required for methylong "
                    "but is missing or empty. Please provide the full path to the reference FASTA."
                ),
            })
        for col in ("path", "ref"):
            p = (row.get(col) or "").strip()
            if not p:
                continue
            if not os.path.isfile(p) and not os.path.isdir(p):
                issues.append({"level": "error", "message": f"Row {i}: file not found — `{p}`"})
            elif os.path.isdir(p) and col == "path":
                # Directory given — verify it contains appropriate files
                entries = [e.name.lower() for e in os.scandir(p)]
                has_pod5 = any(n.endswith(".pod5") for n in entries)
                has_bam  = any(n.endswith(".bam")  for n in entries)
                if not has_pod5 and not has_bam:
                    issues.append({
                        "level": "error",
                        "message": (
                            f"Row {i}: directory `{p}` contains no .pod5 or .bam files. "
                            "ONT requires pod5 files, PacBio requires bam files."
                        ),
                    })
                elif method == "ont" and not has_pod5 and has_bam:
                    pass  # ONT modBAM is valid
                elif method == "pacbio" and not has_bam:
                    issues.append({
                        "level": "error",
                        "message": f"Row {i}: PacBio method but no .bam files found in `{p}`.",
                    })

    # 2. ONT BAM without MM/ML modification tags
    for i, row in enumerate(rows, 1):
        method = (row.get("method") or "").strip().lower()
        path   = (row.get("path")   or "").strip()
        if method == "ont" and path.lower().endswith(".bam") and os.path.isfile(path):
            if not _bam_has_mod_tags(path):
                issues.append({
                    "level": "error",
                    "message": (
                        f"Row {i}: ONT BAM `{os.path.basename(path)}` has no MM/ML "
                        "modification tags. Methylation analysis requires a modBAM "
                        "(basecalled with Dorado + modification model) or pod5 files."
                    ),
                })

    # 3. DMR group validation
    lower_input = user_input.lower()
    wants_dmr = any(k in lower_input for k in _DMR_KEYWORDS)
    wants_hap = any(k in lower_input for k in _HAPLOTYPE_KEYWORDS)
    if wants_dmr and not wants_hap:
        groups: dict[str, list] = {}
        for row in rows:
            g = (row.get("group") or "").strip()
            groups.setdefault(g, []).append(row)
        if len(groups) < 2:
            g_name = list(groups.keys())[0] if groups else "unknown"
            issues.append({
                "level": "error",
                "message": (
                    f"DMR analysis requires ≥ 2 distinct groups, but all samples belong "
                    f"to group '{g_name}'. Please assign samples to at least two groups."
                ),
            })
        else:
            singletons = [g for g, members in groups.items() if len(members) == 1]
            if singletons:
                issues.append({
                    "level": "warning",
                    "message": (
                        f"Groups {singletons} have only 1 sample each. "
                        "Statistical DMR calling needs replicates for robust p-values."
                    ),
                })

    return issues
