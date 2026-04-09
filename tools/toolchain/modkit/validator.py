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

        # 若用户未指定输出路径，自动生成到 out_dir
        if len(pos_args) < 2:
            ts = int(time.time())
            pos_args.append(os.path.join(out_dir, f"modkit_pileup_{ts}.bed"))
        else:
            out_name = os.path.basename(pos_args[1])
            pos_args[1] = os.path.join(out_dir, out_name)

        # 规范化 --ref 路径
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
