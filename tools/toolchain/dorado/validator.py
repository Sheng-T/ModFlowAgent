"""Dorado model registry + command builder."""
import copy
import os
import time
import re
from tools.toolchain.command_builder import build_shell_args
from utils.validator_utils import deduplicate_kwargs

RNA_BASECALL_MODEL = "rna004_130bps_sup@v5.2.0"
RNA_MOD_MODELS = {
    "m6a":              "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    "inosine":          "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    "inosinem6a":       "rna004_130bps_sup@v5.1.0_inosine_m6A@v1",
    "drach":            "rna004_130bps_sup@v5.2.0_m6A_DRACH@v1",
    "m6adrach":         "rna004_130bps_sup@v5.2.0_m6A_DRACH@v1",
    "2omea":            "rna004_130bps_sup@v5.2.0_inosine_m6A_2OmeA@v1",
    "inosinem6a2omea":  "rna004_130bps_sup@v5.2.0_inosine_m6A_2OmeA@v1",
    "pseu":             "rna004_130bps_sup@v5.1.0_pseU@v1",
    "pseudouridine":    "rna004_130bps_sup@v5.1.0_pseU@v1",
    "pseu2omeu":        "rna004_130bps_sup@v5.2.0_pseU_2OmeU@v1",
    "m5c":              "rna004_130bps_sup@v5.1.0_m5C@v1",
    "m5c2omec":         "rna004_130bps_sup@v5.2.0_m5C_2OmeC@v1",
    "2omeg":            "rna004_130bps_sup@v5.2.0_2OmeG@v1",
    "all":              None,
}
DNA_BASECALL_MODEL = "dna_r10.4.1_e8.2_400bps_sup@v5.2.0"
DNA_MOD_MODELS = {
    "cpg":              "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mCG_5hmCG@v1",
    "5mcg":             "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mCG_5hmCG@v1",
    "5mcpg":            "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mCG_5hmCG@v1",
    "5hmcg":            "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mCG_5hmCG@v1",
    "5mcg5hmcg":        "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mCG_5hmCG@v1",
    "5mc":              "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mC_5hmC@v1",
    "5hmc":             "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mC_5hmC@v1",
    "5mc5hmc":          "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_5mC_5hmC@v1",
    "4mc":              "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_4mC_5mC@v1",
    "4mc5mc":           "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_4mC_5mC@v1",
    "6ma":              "dna_r10.4.1_e8.2_400bps_sup@v5.2.0_6mA@v1",
    "all":              None,
}
_DEFAULTS: dict[str, str] = {"RNA": "m6a", "DNA": "cpg"}
_LEGACY_BASECALL_MODEL_ALIASES = {
    "dna_r10.4.1_e8.2_400bps_sup@v5.0.0": DNA_BASECALL_MODEL,
}
_MOD_BASE_SELECTORS = {
    "RNA": {
        "m6a": "m6A",
        "inosine": "inosine_m6A",
        "inosinem6a": "inosine_m6A",
        "drach": "m6A_DRACH",
        "m6adrach": "m6A_DRACH",
        "2omea": "inosine_m6A_2OmeA",
        "inosinem6a2omea": "inosine_m6A_2OmeA",
        "pseu": "pseU",
        "pseudouridine": "pseU",
        "pseu2omeu": "pseU_2OmeU",
        "m5c": "m5C",
        "m5c2omec": "m5C_2OmeC",
        "2omeg": "2OmeG",
    },
    "DNA": {
        "cpg": "5mCG_5hmCG",
        "5mcg": "5mCG_5hmCG",
        "5mcpg": "5mCG_5hmCG",
        "5hmcg": "5mCG_5hmCG",
        "5mcg5hmcg": "5mCG_5hmCG",
        "5mc": "5mC_5hmC",
        "5hmc": "5mC_5hmC",
        "5mc5hmc": "5mC_5hmC",
        "4mc": "4mC_5mC",
        "4mc5mc": "4mC_5mC",
        "6ma": "6mA",
    },
}


def resolve_models(molecule: str, modification_type: str) -> tuple[str, str | None]:
    """Return (basecall_model_name, mod_model_name | None)."""
    mol = molecule.strip().upper()
    mod_key = (modification_type or "").strip().lower()
    mod_key = mod_key.replace("-", "").replace("_", "").replace(" ", "")
    if mol == "RNA":
        basecall = RNA_BASECALL_MODEL
        table = RNA_MOD_MODELS
        default = _DEFAULTS["RNA"]
    else:
        basecall = DNA_BASECALL_MODEL
        table = DNA_MOD_MODELS
        default = _DEFAULTS["DNA"]
    if mod_key in ("none", "basecallonly", "none(basecallonly)"):
        return basecall, None
    if not mod_key or mod_key not in table:
        mod_key = default
    return basecall, table.get(mod_key, table[default])


def list_modifications(molecule: str) -> list[str]:
    """Return user-facing modification options for the given molecule."""
    mol = molecule.strip().upper()
    if mol == "RNA":
        return ["m6adrach", "m6a", "inosine", "2omea", "pseu", "m5c", "2omeg", "none"]
    return ["5mcpg", "5hmcg", "5mc", "5hmc", "4mc", "6ma", "none"]


def _normalize_mod_base_selector(molecule: str, mod_base: str) -> str:
    mol = molecule.strip().upper()
    key = (mod_base or "").strip().lower()
    key = key.replace("-", "").replace("_", "").replace(" ", "")
    return _MOD_BASE_SELECTORS.get(mol, {}).get(key, mod_base)


def _normalize_mod_model_name(model_name: str) -> str:
    base_name = os.path.basename(model_name or "")
    for legacy_base, current_base in _LEGACY_BASECALL_MODEL_ALIASES.items():
        prefix = f"{legacy_base}_"
        if not base_name.startswith(prefix):
            continue
        selector = base_name[len(prefix):].split("@", 1)[0]
        for candidate in DNA_MOD_MODELS.values():
            if candidate and candidate.startswith(f"{current_base}_{selector}@"):
                return candidate
    return base_name


def dorado(subcommand, subcommand_str, args_dict, data_path):
    """Build dorado shell command."""
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    pos_args = args_dict.get("pos_args", [])
    data_dir = data_path["base_data_dir"]
    out_dir  = data_path.get("out_dir", data_dir)

    if not subcommand:
        arg_str = build_shell_args(args_dict)
        return f"dorado {arg_str}".strip()

    if subcommand == "basecaller":
        model_dir = data_path["dorado_models"]
        kwargs.pop("o", None)
        kwargs.pop("output-dir", None)
        if model_dir and not kwargs.get("models-directory"):
            kwargs["models-directory"] = model_dir
        if not kwargs.get("emit-moves"):
            kwargs["emit-moves"] = True
        device = kwargs.get("device", "")
        if not device:
            kwargs["device"] = "auto"
        else:
            device = str(device)
            m = re.match(r"^gpu(?::(\d+(?:,\d+)*))?$", device)
            if m:
                ids = m.group(1)
                device = f"cuda:{ids}" if ids else "cuda"
            if not re.match(r"^(cpu|auto|cuda(?::\d+(?:,\d+)*)?)$", device):
                kwargs["device"] = "auto"
            else:
                kwargs["device"] = device
        ext = "bam"
        if kwargs.get("emit-fastq"):
            ext = "fastq"
        elif kwargs.get("emit-sam"):
            ext = "sam"
        timestamp = int(time.time())
        out_file = os.path.join(out_dir, f"dorado_out_{timestamp}.{ext}")
        model_name = ""
        molecule = "DNA"
        if len(pos_args) >= 1:
            model_name = os.path.basename(pos_args[0])
            model_name = _LEGACY_BASECALL_MODEL_ALIASES.get(model_name, model_name)
            if "rna" in model_name.lower():
                molecule = "RNA"
            pos_args[0] = os.path.join(model_dir, model_name)
        if len(pos_args) >= 2:
            data_input = str(pos_args[1])
            pos_args[1] = (
                data_input
                if os.path.isabs(data_input)
                else os.path.join(data_dir, os.path.basename(data_input))
            )
        mod_base = kwargs.get("modified-bases", "")
        mod_model = kwargs.get("modified-bases-models", "")
        if mod_base and not mod_model:
            kwargs["modified-bases"] = _normalize_mod_base_selector(molecule, str(mod_base))
        elif mod_model:
            kwargs.pop("modified-bases", None)
            kwargs["modified-bases-models"] = os.path.join(model_dir, _normalize_mod_model_name(str(mod_model)))
        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str = build_shell_args(new_args)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str} > {out_file}"
    elif subcommand == "download":
        model_dir = data_path["dorado_models"]
        if "directory" not in kwargs:
            kwargs["directory"] = model_dir
        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str = build_shell_args(new_args)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str}"
    elif subcommand == "summary":
        if not pos_args:
            return "Error: pos_args is empty!"
        reads = pos_args[0]
        timestamp = int(time.time())
        out_file = os.path.join(out_dir, f"{os.path.basename(reads)}_{timestamp}.summary.txt")
        arg_str = build_shell_args(args_dict)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str} > {out_file}"
    else:
        arg_str = build_shell_args(args_dict)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str}"
    return final_raw_cmd
