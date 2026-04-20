"""
LangGraph 持久化 Checkpointer（SqliteSaver 单例）。

使用方:
    from storage.checkpointer import get_checkpointer
    checkpointer = get_checkpointer()

依赖: pip install langgraph-checkpoint-sqlite
退路: 若包未安装则自动降级为 MemorySaver（仅内存，重启丢失）。
"""
import os
import sqlite3

_checkpointer = None


def get_checkpointer():
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    from configs.path_config import OTHER_PATH
    db_path = OTHER_PATH["checkpoint_db"]
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=10000")
        _checkpointer = SqliteSaver(conn)
    except ImportError:
        # langgraph-checkpoint-sqlite 未安装，降级
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer = MemorySaver()
        print(
            "[Checkpointer] 警告: langgraph-checkpoint-sqlite 未安装，使用 MemorySaver（重启后历史丢失）。\n"
            "  安装命令: pip install langgraph-checkpoint-sqlite"
        )

    return _checkpointer
