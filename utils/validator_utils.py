import os


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

def normalize_kwargs(kwargs):
    for k, v in kwargs.items():
        if isinstance(v, str):
            if v.lower() == "true":
                kwargs[k] = True
            elif v.lower() == "false":
                kwargs[k] = False
    return kwargs

def return_arg_by_key_len(key: str):
    if len(key) == 1:
        return f"-{key}"
    return f"--{key}"

def normalize_flag(k):
    return k.lstrip('-')

