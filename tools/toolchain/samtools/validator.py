import copy
import os
import time

from tools.toolchain.command_builder import build_shell_args
from utils.validator_utils import deduplicate_kwargs
def samtools(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    pos_args = args_dict.get("pos_args", [])

    if not subcommand:
        arg_str = build_shell_args(args_dict)
        return f"samtools {arg_str}".strip()

    data_dir = data_path['base_data_dir']
    if subcommand == "sort":
        kwargs['o'] = os.path.join(data_dir, f"sorted_{int(time.time())}.bam")
        new_args = {
            "pos_args": pos_args,
            "kwargs": deduplicate_kwargs(kwargs)
        }

        arg_str = build_shell_args(new_args)
    else:
        arg_str = build_shell_args(args_dict)
    return f"samtools {subcommand_str} {arg_str}"