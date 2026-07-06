from utils.validator_utils import normalize_kwargs, normalize_flag, return_arg_by_key_len


def build_shell_args(args_dict):
    flag_parts = []
    pos_parts = []


    for val in args_dict.get("pos_args", []):
        if val:
            pos_parts.append(str(val))


    kwargs = normalize_kwargs(args_dict.get("kwargs", {}))

    for k, v in kwargs.items():

        k_ = return_arg_by_key_len(normalize_flag(k))
        if isinstance(v, bool):
            if v:
                flag_parts.append(k_)
            continue

        if v is None:
            continue

        if v == "":
            if len(k) == 1:
                flag_parts.append(k_)  
            continue

        if isinstance(v, list):
            for item in v:
                flag_parts.append(f"{k_} {item}")
            continue

        flag_parts.append(f"{k_} {v}")


    all_parts = flag_parts + pos_parts

    return " ".join(all_parts)