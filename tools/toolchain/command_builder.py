from utils.validator_utils import normalize_kwargs, normalize_flag, return_arg_by_key_len


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
    kwargs = normalize_kwargs(args_dict.get("kwargs", {}))

    for k, v in kwargs.items():

        k_ = return_arg_by_key_len(normalize_flag(k))

        # bool 类型
        if isinstance(v, bool):
            if v:
                flag_parts.append(k_)
            continue

        # 跳过空值
        if v is None:
            continue

        if v == "":
            if len(k) == 1:
                flag_parts.append(k_)  # 输出 -v
            continue

        # list → 多参数展开（关键修复）
        if isinstance(v, list):
            for item in v:
                flag_parts.append(f"{k_} {item}")
            continue

        # 普通参数
        flag_parts.append(f"{k_} {v}")

    # ======================
    # 4. 拼接顺序（非常重要）
    # flags → pos_args
    # ======================
    all_parts = flag_parts + pos_parts

    return " ".join(all_parts)