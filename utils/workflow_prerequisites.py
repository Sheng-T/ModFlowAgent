"""
Helpers for workflow prerequisite definitions.

nfcore workflows  → CSV samplesheet prereqs (type "csv")
local workflows   → key-value param form prereqs (type "local_params")
"""
import json
import os

_JSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "workflows", "workflow_prereqs.json"
)

with open(_JSON_PATH, encoding="utf-8") as _f:
    _CONFIG: dict = json.load(_f)


# ── nfcore CSV helpers (existing interface) ────────────────────────────────────

def needs_prereq(pipeline: str) -> bool:
    """True when the pipeline has any prereq (CSV or local_params)."""
    entry = _CONFIG.get(pipeline, {})
    return bool(entry.get("needs_prereq")) and bool(entry.get("prereqs"))


def get_prereqs(pipeline: str) -> list:
    """All prereq definitions for the pipeline (list of dicts)."""
    return _CONFIG.get(pipeline, {}).get("prereqs", [])


def get_csv_prereqs(pipeline: str) -> list:
    """Only CSV-type prereqs (used by generate_prereqs_node for nfcore)."""
    return [p for p in get_prereqs(pipeline) if p.get("type") == "csv"]


# ── local_params helpers ───────────────────────────────────────────────────────

def needs_local_prereq(workflow: str) -> bool:
    """True when the workflow has local_params-type prereqs."""
    entry = _CONFIG.get(workflow, {})
    if not entry.get("needs_prereq"):
        return False
    return any(p.get("type") == "local_params" for p in entry.get("prereqs", []))


def get_local_prereq_params(workflow: str) -> list[dict]:
    """
    Returns the params list for local_params prereqs, e.g.:
    [{"key": "data_file", "label": "...", "required": True, ...}, ...]
    """
    for p in get_prereqs(workflow):
        if p.get("type") == "local_params":
            return p.get("params", [])
    return []


# ── nfcore pre-params helpers ──────────────────────────────────────────────────

def needs_nfcore_pre_params(workflow: str) -> bool:
    """True when an nfcore workflow has a nfcore_pre_params section."""
    return bool(_CONFIG.get(workflow, {}).get("nfcore_pre_params"))


def get_nfcore_pre_params(workflow: str) -> list[dict]:
    """Return the nfcore_pre_params list (platform / molecule selectors)."""
    return _CONFIG.get(workflow, {}).get("nfcore_pre_params", [])
