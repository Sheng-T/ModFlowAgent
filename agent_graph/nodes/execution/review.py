from agent_graph.prompts.review_prompts import build_human_review_feedback_prompt
from agent_graph.state import AgentState
from configs.path_config import DATA_PATH
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import build_command_for_call

# 统一使用顶级 `utils.ui_logger` 导出
from utils.ui_logger import ui_print

def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls = state.get("tool_calls", [])
    user_feedback = state.get("user_feedback", "")
    pending_commands = []
    if user_feedback:
        state["user_feedback"] = ""
    for i, call in enumerate(tool_calls):
        raw_cmd = build_command_for_call(call, is_workflow=state.get("is_workflow", False))
        pending_commands.append(raw_cmd)
        ui_print(f"[Review] 步骤 {i+1}: {raw_cmd}")

    return {
        **state,
        "pending_commands": pending_commands,
        "next_node": "executor",  # ← 必须有这行
    }
