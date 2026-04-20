import os
import threading

# 模块级缓存，进程内只检测一次；用锁保护并发写入
_DORADO_LIB_CACHE: dict[str, str] = {}
_cache_lock = threading.Lock()

def _find_latest_dorado_model(model_dir: str, pattern: str, major_version: int = 0) -> str:
    """
    在 model_dir 下找到匹配 pattern 前缀的目录，返回版本号最大的那个的完整路径。
    找不到时返回空字符串。

    major_version: 若 > 0，只返回主版本号匹配的模型（如 4 → v4.x.x，5 → v5.x.x）。
                   0 表示不过滤，返回最新版本。

    pattern 示例:
      'dna_r10.4.1_e8.2_400bps_sup@v'          → 匹配 simplex 模型
      'dna_r10.4.1_e8.2_400bps_sup@v'_5mC_5hmC → 匹配修饰模型（需另行前缀）
    """
    if not model_dir or not os.path.isdir(model_dir):
        return ""
    import re
    candidates = []
    for name in os.listdir(model_dir):
        if name.startswith(pattern) and os.path.isdir(os.path.join(model_dir, name)):
            # 提取版本号部分，如 v5.0.0 → (5, 0, 0)
            ver_match = re.search(r'@v(\d+)\.(\d+)\.(\d+)', name)
            if ver_match:
                ver = tuple(int(x) for x in ver_match.groups())
                if major_version > 0 and ver[0] != major_version:
                    continue
                candidates.append((ver, os.path.join(model_dir, name)))
    if not candidates:
        return ""
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def _find_dorado_lib_path_in_image(image_path: str) -> str:
    """在镜像内动态找 dorado 库路径，结果缓存到内存。"""
    with _cache_lock:
        if image_path in _DORADO_LIB_CACHE:
            return _DORADO_LIB_CACHE[image_path]

    # 先用预设值兜底
    fallback = "/opt/custflow/epi2meuser/dorado/lib"

    if not image_path or not os.path.exists(image_path):
        with _cache_lock:
            _DORADO_LIB_CACHE[image_path] = fallback
        return fallback

    try:
        import subprocess
        result = subprocess.run(
            ['singularity', 'exec', image_path,
             'find', '/opt', '/usr',
             '-name', 'libdorado_torch_lib.so',
             '-not', '-path', '*/session/*',
             '-not', '-path', '/tmp/*'],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line:
                lib_dir = os.path.dirname(line)
                print(f"[CmdBuilder] Found dorado lib: {lib_dir}")
                with _cache_lock:
                    _DORADO_LIB_CACHE[image_path] = lib_dir
                return lib_dir
    except Exception as e:
        print(f"[CmdBuilder] dorado lib detection failed: {e}, using fallback")

    with _cache_lock:
        _DORADO_LIB_CACHE[image_path] = fallback
    return fallback