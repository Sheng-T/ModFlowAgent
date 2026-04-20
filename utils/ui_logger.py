"""
UI日志桥接工具 - 把节点中的 print 内容传到 Streamlit UI
"""
import queue
import threading

# 全局日志队列，节点写入，UI读取；有界防止内存无限增长
_log_queue = queue.Queue(maxsize=10000)
_lock = threading.Lock()


def ui_print(*args, **kwargs):
    """替换 print，把内容放入队列供UI读取；队列满时丢弃（不阻塞）"""
    msg = " ".join(str(a) for a in args)
    try:
        _log_queue.put_nowait(msg)
    except queue.Full:
        pass  # 队列满时静默丢弃，避免阻塞工作流线程

    # 同时保留终端输出，方便调试
    print(msg, **kwargs)


def get_log_queue():
    """获取日志队列"""
    return _log_queue


def flush_logs():
    """取出队列里所有日志"""
    logs = []
    with _lock:
        while not _log_queue.empty():
            try:
                logs.append(_log_queue.get_nowait())
            except queue.Empty:
                break
    return logs


def clear_logs():
    """清空队列"""
    with _lock:
        while not _log_queue.empty():
            try:
                _log_queue.get_nowait()
            except queue.Empty:
                break
