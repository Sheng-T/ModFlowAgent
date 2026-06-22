"""
ONT modification model registry.

Maps (molecule, modification_type) → (basecall_model, mod_model).

Rules (from dorado model list, v5.2.0 sup preferred):
  DNA:
    - CpG / 5mCG / default → 5mCG_5hmCG (prefer CG-context over generic 5mC)
    - 5mC                   → 5mC_5hmC   (NOT 4mC_5mC, that's for bacterial)
    - 4mC                   → 4mC_5mC    (bacterial methylation, explicit only)
    - 5hmC                  → 5mC_5hmC
    - 6mA                   → 6mA
    - all                   → None (dorado detects all supported)

  RNA:
    - m6A / default         → inosine_m6A   (not m6A_DRACH; inosine_m6A is broader)
    - drach / m6A_DRACH     → m6A_DRACH     (DRACH-context only, explicit request)
    - inosine               → inosine_m6A   (same model)
    - 2OmeA                 → inosine_m6A_2OmeA  (explicit 2'-O-methylation request)
    - pseU / pseudouridine  → pseU
    - m5C                   → m5C
    - 2OmeG                 → 2OmeG
    - all                   → None

Adding a new modification:
  1. Add a row to RNA_MOD_MODELS or DNA_MOD_MODELS.
  2. Add the user-facing option to static/workflow/workflow_prereqs.json.
  3. No other files need changing.
"""
from __future__ import annotations

# ── RNA ───────────────────────────────────────────────────────────────────────
# Basecall: latest sup available
RNA_BASECALL_MODEL = "rna004_130bps_sup@v5.2.0"

# Modification models — use latest sup version that has the modification.
# v5.2.0 sup has: 2OmeG, m5C_2OmeC, inosine_m6A_2OmeA, m6A_DRACH, pseU_2OmeU
# v5.1.0 sup has: m5C, inosine_m6A, m6A_DRACH, pseU   (use when v5.2.0 sup lacks plain variant)
RNA_MOD_MODELS: dict[str, str | None] = {
    # m6A variants (default: inosine_m6A — broadest coverage without 2Ome suffix)
    "m6a":              "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    "inosine":          "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    "inosinem6a":       "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    # DRACH-context m6A (explicit user request)
    "drach":            "rna004_130bps_sup@v5.2.0_m6A_DRACH@v1",
    "m6adrach":         "rna004_130bps_sup@v5.2.0_m6A_DRACH@v1",
    # 2'-O-methylation variants (explicit user request)
    "2omea":            "rna004_130bps_sup@v5.2.0_inosine_m6A_2OmeA@v1",
    "inosinem6a2omea":  "rna004_130bps_sup@v5.2.0_inosine_m6A_2OmeA@v1",
    # pseudouridine
    "pseu":             "rna004_130bps_sup@v5.1.0_pseU@v1",
    "pseudouridine":    "rna004_130bps_sup@v5.1.0_pseU@v1",
    "pseu2omeu":        "rna004_130bps_sup@v5.2.0_pseU_2OmeU@v1",
    # m5C / cytosine methylation
    "m5c":              "rna004_130bps_sup@v5.1.0_m5C@v1",
    "m5c2omec":         "rna004_130bps_sup@v5.2.0_m5C_2OmeC@v1",
    # 2'-O-methylguanosine
    "2omeg":            "rna004_130bps_sup@v5.2.0_2OmeG@v1",
    # detect all supported modifications
    "all":              None,
}

# ── DNA ───────────────────────────────────────────────────────────────────────
DNA_BASECALL_MODEL = "dna_r10.4.1_e8.2_400bps_sup@v5.0.0"

DNA_MOD_MODELS: dict[str, str | None] = {
    # CpG methylation (default) — prefer CG-context model
    "cpg":              "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mCG_5hmCG@v3",
    "5mcg":             "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mCG_5hmCG@v3",
    "5mcpg":            "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mCG_5hmCG@v3",
    "5hmcg":            "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mCG_5hmCG@v3",
    "5mcg5hmcg":        "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mCG_5hmCG@v3",
    # Generic cytosine methylation (non-CG context) — use 5mC_5hmC, NOT 4mC_5mC
    "5mc":              "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mC_5hmC@v3",
    "5hmc":             "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mC_5hmC@v3",
    "5mc5hmc":          "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mC_5hmC@v3",
    # Bacterial / 4mC (only when explicitly requested)
    "4mc":              "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_4mC_5mC@v3",
    "4mc5mc":           "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_4mC_5mC@v3",
    # N6-methyladenine
    "6ma":              "dna_r10.4.1_e8.2_400bps_sup@v5.0.0_6mA@v3",
    # detect all supported modifications
    "all":              None,
}

# ── Defaults ──────────────────────────────────────────────────────────────────
_DEFAULTS: dict[str, str] = {
    "RNA": "m6a",
    "DNA": "cpg",
}


def resolve_models(molecule: str, modification_type: str) -> tuple[str, str | None]:
    """
    Return (basecall_model_name, mod_model_name | None).

    mod_model_name is None when the user requests all modifications,
    or when the type is unrecognised (falls back to molecule default).
    """
    mol = molecule.strip().upper()
    # Normalise: lowercase, strip spaces/hyphens/underscores for key lookup
    mod_key = (modification_type or "").strip().lower()
    mod_key = mod_key.replace("-", "").replace("_", "").replace(" ", "")

    if mol == "RNA":
        basecall = RNA_BASECALL_MODEL
        table    = RNA_MOD_MODELS
        default  = _DEFAULTS["RNA"]
    else:
        basecall = DNA_BASECALL_MODEL
        table    = DNA_MOD_MODELS
        default  = _DEFAULTS["DNA"]

    # "none" / "basecall only" → return basecall model only, no mod model
    if mod_key in ("none", "basecallonly", "none(basecallonly)"):
        return basecall, None

    if not mod_key or mod_key not in table:
        mod_key = default

    return basecall, table.get(mod_key, table[default])


def get_modkit_flags(molecule: str, modification_type: str) -> dict[str, str]:
    """
    Return modkit pileup / extract flag strings for the given modification.

    Keys:
      "pileup_extra"   — extra flags appended to `modkit pileup`  (motif / --cpg)
      "extract_extra"  — extra flags appended to `modkit extract` (motif / --cpg)

    Common flags (-t, --no-filtering) are added by the step builder from TOOL_THREADS.
    """
    mol     = molecule.strip().upper()
    mod_key = (modification_type or "").strip().lower()
    mod_key = mod_key.replace("-", "").replace("_", "").replace(" ", "")

    if mol == "DNA":
        # CpG-context modifications → --cpg shorthand
        if mod_key in ("cpg", "5mcg", "5mcpg", "5hmcg", "5mcg5hmcg", ""):
            return {"pileup_extra": "--cpg", "extract_extra": "--cpg"}
        # Generic cytosine (all C positions)
        if mod_key in ("5mc", "5hmc", "5mc5hmc", "4mc5mc", "4mc"):
            return {"pileup_extra": "--motif C 0", "extract_extra": "--motif C 0"}
        # CHH context
        if mod_key == "chh":
            return {"pileup_extra": "--motif CHH 0", "extract_extra": "--motif CHH 0"}
        # N6-methyladenine
        if mod_key == "6ma":
            return {"pileup_extra": "--motif A 0", "extract_extra": "--motif A 0"}
        # all / none / basecall only → no motif constraint
        return {"pileup_extra": "", "extract_extra": ""}

    # RNA — mod codes from CHEBI / SAM spec (same as ont_rna.py RNA_MOD_CODE_NAMES)
    # DRACH-context m6A only
    if mod_key in ("drach", "m6adrach"):
        return {"pileup_extra": "--motif DRACH 2 --mod-code a",
                "extract_extra": "--motif DRACH 2 --mod-code a"}
    # m6A only (filter out inosine from inosine_m6A model)
    if mod_key == "m6a":
        return {"pileup_extra": "--mod-code a", "extract_extra": "--mod-code a"}
    # inosine only (filter out m6A from inosine_m6A model)
    if mod_key == "inosine":
        return {"pileup_extra": "--mod-code 17596", "extract_extra": "--mod-code 17596"}
    # inosine + m6A together — no filter
    if mod_key == "inosinem6a":
        return {"pileup_extra": "", "extract_extra": ""}
    # 2OmeA only
    if mod_key == "2omea":
        return {"pileup_extra": "--mod-code 69426", "extract_extra": "--mod-code 69426"}
    # inosine + m6A + 2OmeA together — no filter
    if mod_key == "inosinem6a2omea":
        return {"pileup_extra": "", "extract_extra": ""}
    # pseudouridine only (filter out 2OmeU from pseU_2OmeU model)
    if mod_key in ("pseu", "pseudouridine"):
        return {"pileup_extra": "--motif T 0 --mod-code 17802",
                "extract_extra": "--motif T 0 --mod-code 17802"}
    # pseU + 2OmeU together — no filter
    if mod_key == "pseu2omeu":
        return {"pileup_extra": "--motif T 0", "extract_extra": "--motif T 0"}
    # m5C only (filter out 2OmeC from m5C_2OmeC model)
    if mod_key == "m5c":
        return {"pileup_extra": "--motif C 0 --mod-code m",
                "extract_extra": "--motif C 0 --mod-code m"}
    # m5C + 2OmeC together — no filter
    if mod_key == "m5c2omec":
        return {"pileup_extra": "--motif C 0", "extract_extra": "--motif C 0"}
    # 2OmeG
    if mod_key == "2omeg":
        return {"pileup_extra": "--motif G 0 --mod-code 19229",
                "extract_extra": "--motif G 0 --mod-code 19229"}
    # all / none / basecall only
    return {"pileup_extra": "", "extract_extra": ""}


def list_modifications(molecule: str) -> list[str]:
    """Return user-facing modification options for the given molecule."""
    mol = molecule.strip().upper()
    if mol == "RNA":
        return ["m6A", "m6A_DRACH", "inosine_m6A_2OmeA", "pseU", "m5C", "2OmeG", "all"]
    return ["5mCG_5hmCG", "5mC_5hmC", "6mA", "4mC_5mC", "all"]
