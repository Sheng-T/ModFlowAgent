"""
线程本地存储：在 LangGraph 执行期间传递当前用户的会话目录信息。

用法：
  # UI 层（在 app.stream() 前调用）
  from utils.user_context import set_session_context
  set_session_context(uid, session_id, session_dir)

  # 工具层（在 build_command_for_call 等处调用）
  from utils.user_context import get_session_dir, get_or_create_run_dir
  user_dir = get_session_dir()   # 返回用户会话目录，无上下文时返回 None

续跑（resume）用法：
  # UI 层锁定一个已有目录
  from utils.user_context import set_run_dir_override, clear_run_dir_override
  set_run_dir_override(session_id, "/path/to/existing/run_dir")

  # 工具层行为不变，get_or_create_run_dir() 会自动返回锁定的目录
"""
import os
import threading
from datetime import datetime

_local = threading.local()

# session_id -> run_dir  （跨线程共享，供 UI 设置、agent 线程读取）
_RUN_DIR_OVERRIDES: dict[str, str] = {}


# ── session 级续跑覆盖 ────────────────────────────────────────────────────────

def set_run_dir_override(session_id: str, run_dir: str) -> None:
    """锁定指定 run_dir，下次该 session 运行时复用它（用于续跑）。"""
    _RUN_DIR_OVERRIDES[session_id] = run_dir


def clear_run_dir_override(session_id: str) -> None:
    """清除续跑锁定，恢复每次新建 run_dir 的默认行为。"""
    _RUN_DIR_OVERRIDES.pop(session_id, None)


def get_run_dir_override(session_id: str) -> str | None:
    """返回当前锁定的续跑目录，未锁定返回 None。"""
    return _RUN_DIR_OVERRIDES.get(session_id)


# ── 线程上下文 ────────────────────────────────────────────────────────────────

def set_session_context(uid: int, session_id: str, session_dir: str, lang: str = ""):
    """设置当前线程的用户会话上下文。"""
    from configs.i18n_config import DEFAULT_LANG
    _local.uid        = uid
    _local.session_id = session_id
    _local.session_dir = session_dir
    _local.run_dir    = None  # 每次新请求重置，get_or_create_run_dir 决定最终值
    _local.lang       = lang or DEFAULT_LANG  # 空字符串回退到默认，避免后台线程访问 st.session_state


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


def get_thread_lang() -> str | None:
    """返回当前线程绑定的语言设置（后台线程专用，避免访问 st.session_state）。"""
    # Do NOT use `or None` — empty string is falsy but means "lang was stored as empty",
    # which after set_session_context defaults to DEFAULT_LANG anyway.
    val = getattr(_local, "lang", None)
    return val if val else None


def get_or_create_run_dir() -> str | None:
    """
    返回本次运行的目录：
    1. 若已创建（同一请求内复用）→ 直接返回
    2. 若设置了续跑覆盖（set_run_dir_override）→ 使用指定目录
    3. 否则新建 run_{session_id[:8]}_{YYYYmmdd_HHMMSS}
    """
    session_dir = get_session_dir()
    if not session_dir:
        return None

    # 同一次请求内复用
    if getattr(_local, "run_dir", None):
        return _local.run_dir

    # 检查续跑覆盖
    session_id = getattr(_local, "session_id", "unknown")
    override = _RUN_DIR_OVERRIDES.get(session_id)
    if override:
        os.makedirs(override, exist_ok=True)
        _local.run_dir = override
        return override

    # 新建
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"run_{session_id[:8]}_{ts}"
    run_dir = os.path.join(session_dir, run_name)
    os.makedirs(run_dir, exist_ok=True)
    _local.run_dir = run_dir
    return run_dir
