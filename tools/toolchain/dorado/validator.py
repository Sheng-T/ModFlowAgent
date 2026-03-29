import copy
import os
import time

from tools.toolchain.command_builder import build_shell_args
from utils.validator_utils import deduplicate_kwargs


def dorado(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    pos_args = args_dict.get("pos_args", [])
    data_dir = data_path['base_data_dir']

    if not subcommand:
        arg_str = build_shell_args(args_dict)
        return f"dorado {arg_str}".strip()

    if subcommand == "basecaller":
        model_dir = data_path['dorado_models']

        #  删除不允许的参数（在 kwargs 里删！）
        kwargs.pop('o', None)
        kwargs.pop('output-dir', None)

        # 强制参数（只在没有时加）
        if not kwargs.get("emit-moves"):
            kwargs["emit-moves"] = True

        device = kwargs.get("device", "")
        if not device:
            kwargs["device"] = "auto"
        else:
            if device not in ['cpu','auto','cuda']:
                kwargs["device"] = "auto"

        #  输出格式判断（从 kwargs）
        ext = "bam"
        if kwargs.get("emit-fastq"):
            ext = "fastq"
        elif kwargs.get("emit-sam"):
            ext = "sam"

        # 输出路径
        timestamp = int(time.time())
        out_file = os.path.join(data_dir, f"dorado_out_{timestamp}.{ext}")

        # ======================
        # 路径重写（关键！！）
        # ======================
        model_name = ''
        if len(pos_args) >= 1:
            model_name = os.path.basename(pos_args[0])
            pos_args[0] = os.path.join(model_dir, model_name)

        if len(pos_args) >= 2:
            data_name = os.path.basename(pos_args[1])
            pos_args[1] = os.path.join(data_dir, data_name)

        mod_base = kwargs.get("modified-bases", "")
        mod_model = kwargs.get("modified-bases-models", "")

        if mod_base and not mod_model:
            # 用户只指定了 modified-bases → 自动生成模型路径
            kwargs["modified-bases-models"] = os.path.join(model_dir, f"{model_name}_{mod_base}@v1")
            # 删除 modified-bases，避免冲突
            kwargs.pop("modified-bases", None)

        elif mod_model:
            # 用户指定了模型路径 → 确保只用 modified-bases-models
            kwargs.pop("modified-bases", None)
            # 规范化路径（只保留模型文件名，拼接到 model_dir）
            kwargs["modified-bases-models"] = os.path.join(model_dir, os.path.basename(mod_model))


        # 重新组装 args_dict（关键）
        new_args = {
            "pos_args": pos_args,
            "kwargs": deduplicate_kwargs(kwargs)
        }

        arg_str = build_shell_args(new_args)

        final_raw_cmd = f"dorado {subcommand_str} {arg_str} > {out_file}"
    elif subcommand == "summary":
        if not pos_args:
            return "Error: pos_args is empty!"

        reads = pos_args[0]

        timestamp = int(time.time())
        out_file = os.path.join(data_dir, f"{os.path.basename(reads)}_{timestamp}.summary.txt")

        arg_str = build_shell_args(args_dict)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str} > {out_file}"
    else:
        arg_str = build_shell_args(args_dict)
        final_raw_cmd = f"dorado {subcommand_str} {arg_str}"

    return final_raw_cmd