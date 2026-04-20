
def _find_free_gpu(min_free_mb: int = 10000) -> str:
    """
    找到显存空闲最多且超过 min_free_mb 的 GPU，返回 'cuda:N'。
    找不到时返回 'cuda:0' 兜底。
    """
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return "cuda:0"

        best_idx, best_free = 0, 0
        for line in result.stdout.strip().splitlines():
            idx, free = line.strip().split(", ")
            free = int(free)
            if free > best_free:
                best_free = free
                best_idx = int(idx)

        if best_free < min_free_mb:
            print(f"[CmdBuilder] WARNING: No GPU with >{min_free_mb}MB free, using cuda:{best_idx} anyway")
        else:
            print(f"[CmdBuilder] Selected GPU {best_idx} with {best_free}MB free")

        return f"cuda:{best_idx}"

    except Exception as e:
        print(f"[CmdBuilder] GPU detection failed: {e}, fallback to cuda:0")
        return "cuda:0"

