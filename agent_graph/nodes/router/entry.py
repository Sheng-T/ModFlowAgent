from agent_graph.state import AgentState, EMPTY_STATE
from utils.llm_utils import get_llm_instance


def reset_session_state_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    print(f"\n[Router] 正在分析用户输入: '{user_input[:30]}...'")

    history = state.get("chat_history", [])
    return {**EMPTY_STATE, "input": user_input, "chat_history": history}


def classify_intent_route(state: AgentState) -> str:
    user_input = state["input"].lower()
    
    # 检查是否有来自UI的显式路由选择
    if "user_choice" in state and state["user_choice"]:
        choice = state["user_choice"]
        print(f"[Router] 用户选择: {choice}")
        if choice == "answer":
            return "route_to_answer"
        elif choice == "tools":
            return "route_to_tools"
        # else:
        #     return "route_to_answer"

    
    # 1) Direct keyword routing for deterministic behavior
    if any(k in user_input for k in ["nextflow", "nf-core", "workflow", "methylong"]):
        return "route_to_tools"  # workflow也走tools路由
    if any(k in user_input for k in ["dorado", "samtools", "basecall", "sort", "index"]):
        return "route_to_tools"

    # 2) 如果没有显式选择，使用LLM判断
    print("[Router] 正在请求 LLM 进行意图分析...")
    llm = get_llm_instance(is_planner=True, temperature=0.2)

    classification = llm.invoke(
        f"你是一个生物信息学专家助手。请分析用户意图并分类：\n"
        f"- 如果用户要求执行具体的操作（如 basecall、排序、统计、运行工具、运行nextflow/nf-core），返回 'tools'；\n"
        f"- 如果用户是询问生物学概念、生信知识、技术原理（如纳米孔、DNA、测序），返回 'answer'；\n"
        f"- 只有当用户在闲聊、骂人或说与科学完全无关的话时，才返回 'irrelevant'。\n"
        f"注意：只返回单词本身，不要任何标点。\n"
        f"用户输入: {user_input}"
    )

    clean_intent = (
        classification.strip()
        .lower()
        .replace("`", "")
        .replace("json", "")
        .replace("{", "")
        .replace("}", "")
        .replace('"', "")
        .strip()
    )

    mapping = {
        "tools": "tools",
        "tool": "tools",
        "workflow": "tools",  # workflow也走tools
        "llmanswer": "answer",
        "answer": "answer",
        "irrelevant": "irrelevant",
    }
    final_intent = mapping.get(clean_intent, "answer")
    return f"route_to_{final_intent}"


