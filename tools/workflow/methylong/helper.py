import os

from utils.runner_utils import _find_latest_dorado_model


def _resolve_methylong_models(data_path: dict) -> tuple[str, str]:
    """
    返回 (dorado_model_path, dorado_modification_model_path)。
    找不到时返回空字符串。
    """
    model_dir = os.path.abspath(os.path.expanduser(
        data_path.get("dorado", {}).get("dorado_models", "")
        or os.path.expanduser("~/tools/dorado_model/")
    ))
    # sample_rate 4000 → v4.x.x models; 5000 → v5.x.x; 0/unset → latest (no filter)
    sample_rate = int(data_path.get("dorado", {}).get("sample_rate", 0))
    major = 4 if sample_rate == 4000 else (5 if sample_rate == 5000 else 0)
    simplex_model = _find_latest_dorado_model(model_dir, "dna_r10.4.1_e8.2_400bps_sup@v", major_version=major)
    if not simplex_model and major > 0:
        # fallback to latest if no model found for this sample rate
        simplex_model = _find_latest_dorado_model(model_dir, "dna_r10.4.1_e8.2_400bps_sup@v")

    # 修饰模型目录名形如: dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mC_5hmC@v3
    # 用前缀 "dna_r10.4.1_e8.2_400bps_sup@v" + 任意版本 + "_5mC_5hmC@v"
    import re
    mod_model = ""
    if os.path.isdir(model_dir):
        candidates = []
        for name in os.listdir(model_dir):
            if re.match(r'dna_r10\.4\.1_e8\.2_400bps_sup@v\d+\.\d+\.\d+_5mC_5hmC@v\d+', name):
                if os.path.isdir(os.path.join(model_dir, name)):
                    # 按 simplex 版本 + mod 版本排序
                    ver_match = re.search(r'@v(\d+)\.(\d+)\.(\d+)_5mC_5hmC@v(\d+)', name)
                    if ver_match:
                        ver = tuple(int(x) for x in ver_match.groups())
                        if major > 0 and ver[0] != major:
                            continue
                        candidates.append((ver, os.path.join(model_dir, name)))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            mod_model = candidates[0][1]
        # fallback: retry without major filter
        if not mod_model and major > 0:
            for name in os.listdir(model_dir):
                if re.match(r'dna_r10\.4\.1_e8\.2_400bps_sup@v\d+\.\d+\.\d+_5mC_5hmC@v\d+', name):
                    if os.path.isdir(os.path.join(model_dir, name)):
                        ver_match = re.search(r'@v(\d+)\.(\d+)\.(\d+)_5mC_5hmC@v(\d+)', name)
                        if ver_match:
                            ver = tuple(int(x) for x in ver_match.groups())
                            candidates.append((ver, os.path.join(model_dir, name)))
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                mod_model = candidates[0][1]

    return simplex_model, mod_model