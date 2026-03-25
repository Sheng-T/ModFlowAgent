from agent_graph.prompts.review_prompts import build_human_review_feedback_prompt
from agent_graph.state import AgentState
from configs.path_config import DATA_PATH
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import build_command_for_call

def review_execution_plan_node(state: AgentState) -> dict:
    tool_calls = state.get("tool_calls", [])
    history = state.get("chat_history", [])

    print("\n" + "=" * 30 + " 待执行任务确认 " + "=" * 30)
    for i, call in enumerate(tool_calls):
        raw_cmd = build_command_for_call(call, is_workflow=state.get("is_workflow", False))
        print("实际执行命令：")
        print(f"  {raw_cmd}")

    print("\n" + "=" * 76)
    user_input = input("\n[确认确认] 是否执行上述命令？(y/n) 或输入修改意见: ").strip()

    if user_input.lower() == "y":
        history.append({"role": "user", "content": "确认执行，无需修改。"})
        return {
            "next_node": "executor",
            "user_approval": True,
            "user_feedback": "",
            "chat_history": history,
        }

    if user_input.lower() == "exit":
        history.append({"role": "user", "content": "退出当前任务。"})
        return {"next_node": "end_node", "chat_history": history}

    history.append({"role": "user", "content": f"用户修改意见：{user_input}"})
    identified_tools = state.get("identified_tools", [])

    llm = get_llm_instance(is_planner=True)
    prompt = build_human_review_feedback_prompt(user_input, tool_calls, identified_tools)
    raw_decision = llm.invoke(prompt)
    decision_text = raw_decision.content if hasattr(raw_decision, "content") else str(raw_decision)
    decision = decision_text.replace("'", "").replace('"', "").replace(".", "").strip().upper()

    mapping = {"SELECTOR": "tools_selector", "REPLAN": "rag", "REPARAM": "param_generator"}

    return {
        "next_node": mapping.get(decision, "param_generator"),
        "user_feedback": user_input,
        "chat_history": history,
    }
