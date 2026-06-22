import os

from agent_graph.state import AgentState
from utils.nodes_utils import build_command_for_call
from utils.user_context import get_or_create_run_dir
from utils.ui_logger import ui_print


def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls    = state.get("tool_calls", [])
    pre_files     = state.get("pre_files", [])
    user_feedback = state.get("user_feedback", "")
    is_workflow   = state.get("workflow_type", "") == "nfcore"
    pending_commands = []

    if user_feedback:
        state["user_feedback"] = ""

    run_dir = get_or_create_run_dir() or ""

    # ── workflow 前置文件：直接用 Python 写入，不生成 shell heredoc 命令 ────────
    if is_workflow and pre_files and run_dir:
        os.makedirs(run_dir, exist_ok=True)
        for pf in pre_files:
            dest = os.path.join(run_dir, pf["filename"])
            with open(dest, "w", encoding="utf-8") as _f:
                _f.write(pf["content"])
            ui_print(f"[Review] Pre-file written: {pf['filename']} → {dest}")

    # ── 正式执行命令 ───────────────────────────────────────────────────────────
    for i, call in enumerate(tool_calls):
        raw_cmd = build_command_for_call(call, is_workflow=is_workflow)
        pending_commands.append(raw_cmd)
        ui_print(f"[Review] Step {i+1}: {raw_cmd}")

    return {
        **state,
        "pending_commands": pending_commands,
        "run_dir":          run_dir,
        "next_node":        "executor",
    }
