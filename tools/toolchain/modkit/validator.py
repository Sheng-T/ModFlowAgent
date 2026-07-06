import copy
import os
import time

from tools.toolchain.command_builder import build_shell_args
from utils.validator_utils import deduplicate_kwargs


def modkit(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs    = args_dict.get("kwargs", {})
    pos_args  = args_dict.get("pos_args", [])

    if not subcommand:
        arg_str = build_shell_args(args_dict)
        return f"modkit {arg_str}".strip()

    data_dir = data_path.get("base_data_dir", ".")
    out_dir  = data_path.get("out_dir", data_dir)

    if subcommand == "pileup":
        # pos_args: [bam, output]
        if len(pos_args) >= 1:
            bam_name = os.path.basename(pos_args[0])
            pos_args[0] = os.path.join(data_dir, bam_name)

        if len(pos_args) < 2:
            ts = int(time.time())
            pos_args.append(os.path.join(out_dir, f"modkit_pileup_{ts}.bed"))
        else:
            out_name = os.path.basename(pos_args[1])
            pos_args[1] = os.path.join(out_dir, out_name)

        ref = kwargs.get("ref", "")
        if ref:
            kwargs["ref"] = os.path.join(data_dir, os.path.basename(ref))

        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str  = build_shell_args(new_args)

    elif subcommand == "extract":
        if len(pos_args) >= 1:
            bam_name = os.path.basename(pos_args[0])
            pos_args[0] = os.path.join(data_dir, bam_name)
        if len(pos_args) < 2:
            ts = int(time.time())
            pos_args.append(os.path.join(out_dir, f"modkit_extract_{ts}.tsv"))
        else:
            out_name = os.path.basename(pos_args[1])
            pos_args[1] = os.path.join(out_dir, out_name)

        # --full produces per-read output required by RnaM6aAnalyzer
        kwargs.setdefault("full", True)

        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str  = build_shell_args(new_args)

    elif subcommand == "summary":
        if len(pos_args) >= 1:
            bam_name = os.path.basename(pos_args[0])
            pos_args[0] = os.path.join(data_dir, bam_name)
        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str  = build_shell_args(new_args)

    elif subcommand == "adjust-mods":
        if len(pos_args) >= 1:
            pos_args[0] = os.path.join(data_dir, os.path.basename(pos_args[0]))
        if len(pos_args) < 2:
            ts = int(time.time())
            pos_args.append(os.path.join(out_dir, f"modkit_adjusted_{ts}.bam"))
        else:
            pos_args[1] = os.path.join(out_dir, os.path.basename(pos_args[1]))

        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str  = build_shell_args(new_args)

    else:
        arg_str = build_shell_args(args_dict)

    return f"modkit {subcommand_str} {arg_str}".strip()


def get_modkit_flags(molecule: str, modification_type: str) -> dict[str, str]:
    """Return modkit pileup / extract flag strings for the given modification.
    Keys: pileup_extra, extract_extra (flags appended to the subcommand).
    """
    mol = molecule.strip().upper()
    mod_key = (modification_type or "").strip().lower()
    mod_key = mod_key.replace("-", "").replace("_", "").replace(" ", "")

    if mol == "DNA":
        if mod_key in ("cpg", "5mcg", "5mcpg", "5hmcg", "5mcg5hmcg", ""):
            return {"pileup_extra": "--cpg", "extract_extra": "--cpg"}
        if mod_key in ("5mc", "5hmc", "5mc5hmc", "4mc5mc", "4mc"):
            return {"pileup_extra": "--motif C 0", "extract_extra": "--motif C 0"}
        if mod_key == "chh":
            return {"pileup_extra": "--motif CHH 0", "extract_extra": "--motif CHH 0"}
        if mod_key == "6ma":
            return {"pileup_extra": "--motif A 0", "extract_extra": "--motif A 0"}
        return {"pileup_extra": "", "extract_extra": ""}

    if mod_key in ("drach", "m6adrach"):
        return {"pileup_extra": "--motif DRACH 2 --mod-code a",
                "extract_extra": "--motif DRACH 2 --mod-code a"}
    if mod_key == "m6a":
        return {"pileup_extra": "--mod-code a", "extract_extra": "--mod-code a"}
    if mod_key == "inosine":
        return {"pileup_extra": "--mod-code 17596", "extract_extra": "--mod-code 17596"}
    if mod_key == "inosinem6a":
        return {"pileup_extra": "", "extract_extra": ""}
    if mod_key == "2omea":
        return {"pileup_extra": "--mod-code 69426", "extract_extra": "--mod-code 69426"}
    if mod_key == "inosinem6a2omea":
        return {"pileup_extra": "", "extract_extra": ""}
    if mod_key in ("pseu", "pseudouridine"):
        return {"pileup_extra": "--motif T 0 --mod-code 17802",
                "extract_extra": "--motif T 0 --mod-code 17802"}
    if mod_key == "pseu2omeu":
        return {"pileup_extra": "--motif T 0", "extract_extra": "--motif T 0"}
    if mod_key == "m5c":
        return {"pileup_extra": "--motif C 0 --mod-code m",
                "extract_extra": "--motif C 0 --mod-code m"}
    if mod_key == "m5c2omec":
        return {"pileup_extra": "--motif C 0", "extract_extra": "--motif C 0"}
    if mod_key == "2omeg":
        return {"pileup_extra": "--motif G 0 --mod-code 19229",
                "extract_extra": "--motif G 0 --mod-code 19229"}
    return {"pileup_extra": "", "extract_extra": ""}
