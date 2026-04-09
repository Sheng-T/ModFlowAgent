"""
从 workflow_prereqs.json 加载 workflow 前置文件配置。

对外暴露：
  needs_prereq(pipeline: str) -> bool
  get_prereqs(pipeline: str) -> list[dict]   # 返回前置文件定义列表
"""
import json
import os

_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "workflow", "workflow_prereqs.json"
)

with open(_JSON_PATH, encoding="utf-8") as _f:
    _CONFIG: dict = json.load(_f)


def needs_prereq(pipeline: str) -> bool:
    """该 pipeline 是否需要生成前置文件。"""
    entry = _CONFIG.get(pipeline, {})
    return bool(entry.get("needs_prereq")) and bool(entry.get("prereqs"))


def get_prereqs(pipeline: str) -> list:
    """返回该 pipeline 的前置文件定义列表，无则返回空列表。"""
    return _CONFIG.get(pipeline, {}).get("prereqs", [])
