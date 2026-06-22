"""
用户文件管理器

目录结构：
  {user_data_root}/
      {uid}/                        ← 用户根目录（用整数 uid，不暴露用户名）
          {session_id}/             ← 会话隔离目录
              sample.fastq
              samplesheet.csv
          {session_id_2}/
              ...

外部调用只需传 uid（int）和 session_id（str），不涉及用户名。
"""
import hashlib
import os
import shutil
import threading
from typing import Dict, List, Optional

# 每个用户一把锁，防止并发上传时配额竞态
_user_locks: dict[int, threading.Lock] = {}
_locks_meta = threading.Lock()

def file_hash(file):
    return hashlib.md5(file.getvalue()).hexdigest()

def _dir_size(path: str) -> int:
    """递归计算目录大小（字节）。"""
    total = 0
    for entry in os.scandir(path):
        if entry.is_file(follow_symlinks=False):
            total += entry.stat().st_size
        elif entry.is_dir(follow_symlinks=False):
            total += _dir_size(entry.path)
    return total


def fmt_size(n: int) -> str:
    """将字节数格式化为人类可读字符串。"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


class FileManager:
    def __init__(self, user_data_root: str, quota_bytes: int):
        self.root = user_data_root
        self.quota = quota_bytes
        os.makedirs(self.root, exist_ok=True)

    # ── 锁工具 ────────────────────────────────────────────────────────────────

    def _user_lock(self, uid: int) -> threading.Lock:
        """返回该用户专属锁，确保配额检查与写入是原子操作。"""
        with _locks_meta:
            if uid not in _user_locks:
                _user_locks[uid] = threading.Lock()
            return _user_locks[uid]

    # ── 目录工具 ───────────────────────────────────────────────────────────────

    def user_dir(self, uid: int) -> str:
        p = os.path.join(self.root, str(uid))
        os.makedirs(p, exist_ok=True)
        return p

    def session_dir(self, uid: int, session_id: str) -> str:
        p = os.path.join(self.user_dir(uid), session_id)
        os.makedirs(p, exist_ok=True)
        return p

    # ── 写入 ──────────────────────────────────────────────────────────────────

    def save_file(self, uid: int, session_id: str, filename: str, data) -> str:
        """保存上传文件，返回服务器绝对路径。配额不足时抛出 ValueError。
        data 可以是 bytes 或任何支持 read() 的类文件对象（流式写入，不占满内存）。
        """
        with self._user_lock(uid):
            return self._save_file_locked(uid, session_id, filename, data)

    def _save_file_locked(self, uid: int, session_id: str, filename: str, data) -> str:
        """save_file 的实际实现，调用前须持有用户锁。"""
        usage = self.get_usage(uid)
        safe_name = os.path.basename(filename)
        if not safe_name:
            raise ValueError(f"Invalid filename: {filename!r}")
        dest = os.path.join(self.session_dir(uid, session_id), safe_name)

        if isinstance(data, (bytes, bytearray)):
            if usage["total_bytes"] + len(data) > self.quota:
                raise ValueError(
                    f"存储配额不足：已用 {fmt_size(usage['total_bytes'])}，"
                    f"配额 {fmt_size(self.quota)}"
                )
            with open(dest, "wb") as f:
                f.write(data)
        else:
            # 流式写入：边写边检查配额，超出则删除已写部分
            written = 0
            chunk = 8 * 1024 * 1024  # 8 MB per chunk
            try:
                with open(dest, "wb") as f:
                    while True:
                        buf = data.read(chunk)
                        if not buf:
                            break
                        if usage["total_bytes"] + written + len(buf) > self.quota:
                            raise ValueError(
                                f"存储配额不足：已用 {fmt_size(usage['total_bytes'])}，"
                                f"配额 {fmt_size(self.quota)}"
                            )
                        f.write(buf)
                        written += len(buf)
            except Exception:
                if os.path.exists(dest):
                    os.unlink(dest)
                raise
        return dest

    # ── 查询 ──────────────────────────────────────────────────────────────────

    def list_session_files(self, uid: int, session_id: str) -> List[Dict]:
        """列出会话目录下所有文件，返回 [{name, path, size}]。"""
        d = os.path.join(self.user_dir(uid), session_id)
        if not os.path.isdir(d):
            return []
        return [
            {"name": e.name, "path": e.path, "size": e.stat().st_size}
            for e in sorted(os.scandir(d), key=lambda x: x.name)
            if e.is_file()
        ]

    def get_usage(self, uid: int) -> Dict:
        """
        返回用户存储用量。
        {
          "total_bytes": int,
          "sessions": {session_id: bytes, ...}
        }
        """
        udir = os.path.join(self.root, str(uid))
        if not os.path.isdir(udir):
            return {"total_bytes": 0, "sessions": {}}
        sessions: Dict[str, int] = {}
        for entry in os.scandir(udir):
            if entry.is_dir():
                sessions[entry.name] = _dir_size(entry.path)
        return {"total_bytes": sum(sessions.values()), "sessions": sessions}

    # ── 删除 ──────────────────────────────────────────────────────────────────

    def delete_file(self, uid: int, session_id: str, filename: str) -> bool:
        fp = os.path.join(self.user_dir(uid), session_id, os.path.basename(filename))
        if os.path.isfile(fp):
            os.remove(fp)
            return True
        return False

    def delete_session_files(self, uid: int, session_id: str):
        """删除整个会话目录（清空该会话所有文件）。"""
        sdir = os.path.join(self.user_dir(uid), session_id)
        if os.path.isdir(sdir):
            shutil.rmtree(sdir)

    def delete_session_run_dirs(self, uid: int, session_id: str):
        """只删除会话目录下的 run_* 子目录（保留用户上传文件）。"""
        sdir = os.path.join(self.user_dir(uid), session_id)
        if not os.path.isdir(sdir):
            return
        for entry in os.scandir(sdir):
            if entry.is_dir() and entry.name.startswith("run_"):
                shutil.rmtree(entry.path, ignore_errors=True)

    def get_session_breakdown(self, uid: int, session_id: str) -> Dict:
        """
        返回会话存储分类统计：
        {
          "upload_bytes": int,   # 直接在 session_dir 下的文件（用户上传）
          "run_bytes":    int,   # run_* 子目录（流水线产物）
          "run_dirs":     [{"name": str, "size": int}],
        }
        """
        sdir = os.path.join(self.user_dir(uid), session_id)
        if not os.path.isdir(sdir):
            return {"upload_bytes": 0, "run_bytes": 0, "run_dirs": []}

        upload_bytes = 0
        run_bytes    = 0
        run_dirs: list = []

        for entry in os.scandir(sdir):
            if entry.is_file(follow_symlinks=False):
                upload_bytes += entry.stat().st_size
            elif entry.is_dir() and entry.name.startswith("run_"):
                sz = _dir_size(entry.path)
                run_bytes += sz
                run_dirs.append({"name": entry.name, "size": sz})

        run_dirs.sort(key=lambda x: x["name"])
        return {"upload_bytes": upload_bytes, "run_bytes": run_bytes, "run_dirs": run_dirs}


# ── 模块级单例 ────────────────────────────────────────────────────────────────

_fm: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    global _fm
    if _fm is None:
        from configs.path_config import OTHER_PATH, USER_QUOTA_BYTES
        _fm = FileManager(OTHER_PATH["user_data_root"], USER_QUOTA_BYTES)
    return _fm
