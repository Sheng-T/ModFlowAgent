import copy
import os
import time


def return_arg_by_key_len(key: str):
    if len(key) == 1:
        return f"-{key}"
    return f"--{key}"

def normalize_flag(k):
    return k.lstrip('-')

def build_shell_args(args_dict):
    flag_parts = []
    pos_parts = []

    # ======================
    # 1. 处理 positional args
    # ======================
    for val in args_dict.get("pos_args", []):
        if val:
            pos_parts.append(str(val))

    # ======================
    # 2. 处理 kwargs（核心修复点）
    # ======================
    kwargs = args_dict.get("kwargs", {})

    for k, v in kwargs.items():
        if k == "extra_args":
            continue

        k_ = return_arg_by_key_len(normalize_flag(k))

        # bool 类型
        if isinstance(v, bool):
            if v:
                flag_parts.append(k_)
            continue

        # 跳过空值
        if v in [None, ""]:
            continue

        # list → 多参数展开（关键修复）
        if isinstance(v, list):
            for item in v:
                flag_parts.append(f"{k_} {item}")
            continue

        # 普通参数
        flag_parts.append(f"{k_} {v}")

    # ======================
    # 3. 处理 extra_args（安全展开）
    # ======================
    extra = kwargs.get("extra_args", "")
    if extra:
        flag_parts.extend(extra.strip().split())

    # ======================
    # 4. 拼接顺序（非常重要）
    # flags → pos_args
    # ======================
    all_parts = flag_parts + pos_parts

    return " ".join(all_parts)


def normalize_path(p, base_dir):
    if not p:
        return p
    return os.path.join(base_dir, os.path.basename(p))

def deduplicate_kwargs(kwargs):
    new_kwargs = {}
    for k, v in kwargs.items():
        norm_k = normalize_flag(normalize_flag(k))  # 统一成 emit-moves 这种格式
        new_kwargs[norm_k] = v
    return new_kwargs

def dorado(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    pos_args = args_dict.get("pos_args", [])
    data_dir = data_path['base_data_dir']




    if subcommand == "basecaller":
        #  删除不允许的参数（在 kwargs 里删！）
        kwargs.pop('o', None)
        kwargs.pop('output-dir', None)

        # 强制参数（只在没有时加）
        if not kwargs.get("emit-moves"):
            kwargs["emit-moves"] = True

        # 自动补 m6A 模型（很关键！）
        if kwargs.get("modified-bases") == "m6A_DRACH":
            if not kwargs.get("modified-bases-models"):
                model = pos_args[0] if pos_args else ""
                if model:
                    kwargs["modified-bases-models"] = f"{model}_m6A@v1"

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
        if len(pos_args) >= 1:
            model_dir = data_path['dorado_models']
            model_name = os.path.basename(pos_args[0])
            pos_args[0] = os.path.join(model_dir, model_name)

        if len(pos_args) >= 2:
            data_name = os.path.basename(pos_args[1])
            pos_args[1] = os.path.join(data_dir, data_name)

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


def samtools(subcommand, subcommand_str, args_dict, data_path):
    args_dict = copy.deepcopy(args_dict)
    kwargs = args_dict.get("kwargs", {})
    pos_args = args_dict.get("pos_args", [])

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

