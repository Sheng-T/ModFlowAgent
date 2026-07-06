
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
            "[Checkpointer] Warning: Langgraph checkpoint sqlite is not installed, using CacheSaver (history lost after restart). \n"
            "Installation command: pip install langgraph checkpoint sqlite"
        )

    return _checkpointer
