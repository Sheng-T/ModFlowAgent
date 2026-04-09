"""
线程本地存储：在 LangGraph 执行期间传递当前用户的会话目录信息。

用法：
  # UI 层（在 app.stream() 前调用）
  from utils.user_context import set_session_context
  set_session_context(uid, session_id, session_dir)

  # 工具层（在 build_command_for_call 等处调用）
  from utils.user_context import get_session_dir, get_or_create_run_dir
  user_dir = get_session_dir()   # 返回用户会话目录，无上下文时返回 None
"""
import os
import threading
from datetime import datetime

_local = threading.local()


def set_session_context(uid: int, session_id: str, session_dir: str):
    """设置当前线程的用户会话上下文。"""
    _local.uid = uid
    _local.session_id = session_id
    _local.session_dir = session_dir
    _local.run_dir = None  # 每次新请求重置 run_dir


def get_session_dir() -> str | None:
    """返回当前线程绑定的用户会话目录，未设置则返回 None。"""
    return getattr(_local, "session_dir", None)


def get_uid() -> int | None:
    return getattr(_local, "uid", None)


def get_session_id() -> str | None:
    return getattr(_local, "session_id", None)


def get_run_dir() -> str | None:
    """返回本次请求已创建的运行目录（未创建则返回 None）。"""
    return getattr(_local, "run_dir", None)


def get_or_create_run_dir() -> str | None:
    """
    在用户会话目录下创建（或复用）本次运行的临时目录。
    格式：run_{session_id[:8]}_{YYYYmmdd_HHMMSS}
    若未设置会话上下文则返回 None。
    """
    session_dir = get_session_dir()
    if not session_dir:
        return None

    # 同一次请求复用同一个 run_dir
    if getattr(_local, "run_dir", None):
        return _local.run_dir

    session_id = getattr(_local, "session_id", "unknown")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"run_{session_id[:8]}_{ts}"
    run_dir = os.path.join(session_dir, run_name)
    os.makedirs(run_dir, exist_ok=True)
    _local.run_dir = run_dir
    return run_dir
