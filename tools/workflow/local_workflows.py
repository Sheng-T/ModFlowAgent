"""
Thin compatibility shim — local workflow definitions now live in registry.py.
This file is kept so any external tooling that imported LOCAL_WORKFLOW_NAMES
or the helper functions continues to work without changes.
"""
from tools.workflow.registry import get, local_names

LOCAL_WORKFLOW_NAMES: set[str] = set(local_names())


def get_local_workflow(name: str) -> dict | None:
    spec = get(name.lower())
    if spec is None or spec.type != "local":
        return None
    return {
        "display_name":  spec.display_name,
        "description":   spec.description,
        "steps":         list(spec.steps),
        "step_tools":    list(spec.step_tools),
        "molecule":      spec.molecule,
        "modification":  spec.modification,
        "input_formats": list(spec.input_formats),
    }


def get_unique_step_tools(workflow_name: str) -> list[str]:
    spec = get(workflow_name.lower())
    if spec is None or spec.type != "local":
        return []
    seen: set[str] = set()
    result: list[str] = []
    for tool in spec.step_tools:
        if tool not in seen:
            seen.add(tool)
            result.append(tool)
    return result
