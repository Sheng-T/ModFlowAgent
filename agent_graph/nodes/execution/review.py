import os
import re

from agent_graph.state import AgentState
from utils.nodes_utils import build_command_for_call
from utils.user_context import get_or_create_run_dir
from utils.ui_logger import ui_print


def _make_review_command(raw_cmd: str, run_dir: str = "") -> str:
    cmd = (raw_cmd or "").strip()
    if not cmd:
        return cmd

    if run_dir:
        cmd = cmd.replace(run_dir, "{run_dir}")

    if "|| (" in cmd and cmd.startswith("[ -f "):
        cmd = cmd.split("|| (", 1)[1].strip()
        if cmd.endswith(")"):
            cmd = cmd[:-1].rstrip()

    cmd = re.sub(r'^\s*:\s+"[^"]+"\s*;\s*', "", cmd).strip()
    cmd = re.sub(r'\s*&&\s*touch\s+"[^"]+"\s*$', "", cmd).strip()
    return cmd


def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls    = state.get("tool_calls", [])
    pre_files     = state.get("pre_files", [])
    user_feedback = state.get("user_feedback", "")
    is_workflow   = state.get("workflow_type", "") == "nfcore"
    pending_commands = []
    review_commands = []

    if user_feedback:
        state["user_feedback"] = ""

    run_dir = get_or_create_run_dir() or ""

    if is_workflow and pre_files and run_dir:
        os.makedirs(run_dir, exist_ok=True)
        for pf in pre_files:
            dest = os.path.join(run_dir, pf["filename"])
            with open(dest, "w", encoding="utf-8") as _f:
                _f.write(pf["content"])
            ui_print(f"[Review] Pre-file written: {pf['filename']} → {dest}")

    for i, call in enumerate(tool_calls):
        raw_cmd = build_command_for_call(call, is_workflow=is_workflow)
        pending_commands.append(raw_cmd)
        review_commands.append(_make_review_command(raw_cmd, run_dir))
        ui_print(f"[Review] Step {i+1}: {raw_cmd}")

    return {
        **state,
        "pending_commands": pending_commands,
        "review_commands": review_commands,
        "run_dir":          run_dir,
        "next_node":        "executor",
    }
