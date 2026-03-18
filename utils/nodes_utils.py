from typing import List, Dict


def format_history(history: List[Dict[str, str]]) -> str:
    """将历史字典转化为 LLM 易读的文本"""
    if not history:
        return "无"
    return "\n".join([f"[{msg['role']}]: {msg['content']}" for msg in history])

