import os

from agent_graph.state import AgentState
from utils.nodes_utils import build_command_for_call
from utils.user_context import get_or_create_run_dir
from utils.ui_logger import ui_print


def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls    = state.get("tool_calls", [])
    pre_files     = state.get("pre_files", [])
    user_feedback = state.get("user_feedback", "")
    is_workflow   = state.get("is_workflow", False)
    pending_commands = []

    if user_feedback:
        state["user_feedback"] = ""

    run_dir = get_or_create_run_dir() or ""

    # ── workflow 前置文件：生成 heredoc 写入命令，可直接在 shell 执行 ──────────
    if is_workflow and pre_files and run_dir:
        for pf in pre_files:
            dest = os.path.join(run_dir, pf["filename"])
            # heredoc 写法：内容原样保留，不需要转义单引号或换行
            heredoc_marker = "SAMPLESHEET_EOF"
            write_cmd = f"cat > {dest} << '{heredoc_marker}'\n{pf['content']}\n{heredoc_marker}"
            pending_commands.append(write_cmd)
            ui_print(f"[Review] 前置文件写入命令已生成: {pf['filename']} → {dest}")

    # ── 正式执行命令 ───────────────────────────────────────────────────────────
    for i, call in enumerate(tool_calls):
        raw_cmd = build_command_for_call(call, is_workflow=is_workflow)
        pending_commands.append(raw_cmd)
        ui_print(f"[Review] 步骤 {i+1}: {raw_cmd}")

    return {
        **state,
        "pending_commands": pending_commands,
        "run_dir":          run_dir,
        "next_node":        "executor",
    }
