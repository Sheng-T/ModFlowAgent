import os

from configs.path_config import PROJECT_ROOT
from utils.config_utils import load_tool_config

STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
VECTOR_DB_DIR = os.path.join(STATIC_DIR, "vector_db_cache")

# configs/tool_config.py

# 普通工具：自动发现 static/tools/ 子目录
TOOLS_DIR = os.path.join(STATIC_DIR, "tools")

def _autodiscover_tools(tools_dir: str) -> tuple[dict, dict, dict, dict]:
    docs, args, caches, rules = {}, {}, {}, {}
    if not os.path.isdir(tools_dir):
        return docs, args, caches
    for name in os.listdir(tools_dir):
        path = os.path.join(tools_dir, name)
        if not os.path.isdir(path):
            continue
        for fname in os.listdir(path):
            if fname.endswith("_doc.md"):
                docs[name] = os.path.join(path, fname)
            if fname.endswith("_args.json"):
                args[name] = load_tool_config(os.path.join(path, fname))
            if fname.endswith("_rules.md"):
                rules[name] = os.path.join(path, fname)
        caches[name] = os.path.join(VECTOR_DB_DIR, "tools", name)
    return docs, args, caches, rules

TOOLS_DOC, TOOLS_ARGS, TOOL_CACHE_DIRS, TOOLS_RULES = _autodiscover_tools(TOOLS_DIR)

# workflows 单独管理
WORKFLOWS_DIR = os.path.join(STATIC_DIR, "workflows")
WORKFLOWS_CACHE_DIR = os.path.join(VECTOR_DB_DIR, "workflows")  # vector_db_cache/workflows

def _autodiscover_workflows(workflows_dir: str) -> tuple[dict, dict, dict, dict]:
    import json as _json
    docs, args, caches, manifests = {}, {}, {}, {}
    if not os.path.isdir(workflows_dir):
        return docs, args, caches, manifests
    for name in os.listdir(workflows_dir):
        path = os.path.join(workflows_dir, name)
        if not os.path.isdir(path):
            continue
        for fname in os.listdir(path):
            fpath = os.path.join(path, fname)
            if fname.endswith("_doc.md"):
                docs[name] = fpath
            elif fname.endswith("_args.json"):
                args[name] = load_tool_config(fpath)
            elif fname.endswith("_manifest.json"):
                try:
                    with open(fpath, encoding="utf-8") as _f:
                        manifests[name] = _json.load(_f)
                except Exception as e:
                    print(f"[Config] Warning: failed to load {fpath}: {e}")
        caches[name] = os.path.join(VECTOR_DB_DIR, "workflows", name)
    return docs, args, caches, manifests

WORKFLOW_PIPELINE_DOCS, WORKFLOW_PIPELINE_ARGS, WORKFLOW_CACHE_DIRS, WORKFLOW_MANIFESTS = _autodiscover_workflows(WORKFLOWS_DIR)
RAG_INSTANCES = {}
