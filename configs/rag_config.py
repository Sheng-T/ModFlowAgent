import os

from configs.path_config import PROJECT_ROOT
from utils.config_utils import load_tool_config

STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
VECTOR_DB_DIR = os.path.join(STATIC_DIR, "vector_db_cache")

# configs/tool_config.py

# 普通工具：自动发现，跳过 workflows 目录
def _autodiscover_tools(static_dir: str) -> tuple[dict, dict, dict]:
    skip = {"vector_db_cache", "workflow"}  # 注意你的目录叫 workflow 不是 workflows
    docs, args, caches = {}, {}, {}
    for name in os.listdir(static_dir):
        path = os.path.join(static_dir, name)
        if not os.path.isdir(path) or name in skip:
            continue
        for fname in os.listdir(path):
            if fname.endswith("_doc.md"):
                docs[name] = os.path.join(path, fname)
            if fname.endswith("_args.json"):
                args[name] = load_tool_config(os.path.join(path, fname))
        caches[name] = os.path.join(VECTOR_DB_DIR, name)  # vector_db_cache/dorado
    return docs, args, caches

TOOLS_DOC, TOOL_ARGS, TOOL_CACHE_DIRS = _autodiscover_tools(STATIC_DIR)

# workflows 单独管理
WORKFLOWS_DIR = os.path.join(STATIC_DIR, "workflow")
WORKFLOWS_DOC = os.path.join(WORKFLOWS_DIR, "workflow_doc.md")
WORKFLOWS_CACHE_DIR = os.path.join(VECTOR_DB_DIR, "workflow")  # vector_db_cache/workflow

def _autodiscover_workflows(workflows_dir: str) -> tuple[dict, dict, dict]:
    docs, args, caches = {}, {}, {}
    for name in os.listdir(workflows_dir):
        path = os.path.join(workflows_dir, name)
        if not os.path.isdir(path):
            continue
        for fname in os.listdir(path):
            if fname.endswith("_doc.md"):
                docs[name] = os.path.join(path, fname)
            if fname.endswith("_args.json"):
                args[name] = load_tool_config(os.path.join(path, fname))
        caches[name] = os.path.join(VECTOR_DB_DIR, "workflow", name)  # vector_db_cache/workflow/methylong
    return docs, args, caches

WORKFLOW_PIPELINE_DOCS, WORKFLOW_PIPELINE_ARGS, WORKFLOW_CACHE_DIRS = _autodiscover_workflows(WORKFLOWS_DIR)

RAG_INSTANCES = {}
