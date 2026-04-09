import copy
import os
import time

from tools.toolchain.command_builder import build_shell_args
from utils.validator_utils import deduplicate_kwargs


def fastqc(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs    = args_dict.get("kwargs", {})
    pos_args  = args_dict.get("pos_args", [])

    data_dir = data_path.get("base_data_dir", ".")
    out_dir  = data_path.get("out_dir", data_dir)

    if not subcommand or subcommand == "run":
        # 规范化输入文件路径
        pos_args = [
            os.path.join(data_dir, os.path.basename(p)) for p in pos_args
        ]

        # 若用户未指定输出目录，默认写到 out_dir
        if not kwargs.get("outdir"):
            kwargs["outdir"] = out_dir

        new_args = {"pos_args": pos_args, "kwargs": deduplicate_kwargs(kwargs)}
        arg_str  = build_shell_args(new_args)

        # fastqc 本身没有子命令，直接拼接
        return f"fastqc {arg_str}".strip()

    # 兜底
    arg_str = build_shell_args(args_dict)
    return f"fastqc {subcommand_str} {arg_str}".strip()
