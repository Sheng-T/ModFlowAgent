from agent_graph.state import AgentState, EMPTY_STATE
from utils.llm_utils import get_llm_instance


def reset_session_state_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    print(f"\n[Router] 正在分析用户输入: '{user_input[:30]}...'")

    history = state.get("chat_history", [])
    # user_choice 必须保留，否则 classify_intent_route 和 select_tools_node 里的模式判断会失效
    user_choice = state.get("user_choice")
    return {**EMPTY_STATE, "input": user_input, "chat_history": history, "user_choice": user_choice}


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
        elif choice == "workflow":
            return "route_to_tools"   # workflow 也走 tools 路由，selector 里会强制 is_workflow=True
        # auto: 继续走下方 LLM 判断

    # 1) Direct keyword routing for deterministic behavior
    _workflow_kw = ["nextflow", "nf-core", "workflow", "pipeline", "流水线", "流程",
                    "methylong", "rnaseq", "methylseq", "sarek", "ampliseq", "mag", "taxprofiler"]
    if any(k in user_input for k in _workflow_kw):
        return "route_to_tools"  # workflow 也走 tools 路由
    if any(k in user_input for k in ["dorado", "samtools", "basecall", "sort", "index"]):
        return "route_to_tools"

    # 2) 如果没有显式选择，使用LLM判断
    print("[Router] 正在请求 LLM 进行意图分析...")
    llm = get_llm_instance(is_planner=True, temperature=0.2)

    classification = llm.invoke(
        f"你是一个生物信息学专家助手。请分析用户意图并分类：\n"
        f"- 如果用户要求执行具体操作、数据分析、运行工具或流水线（包括但不限于：basecall、排序、甲基化分析、转录组分析、变异检测、提供了测序文件要求分析），返回 'tools'；\n"
        f"- 如果用户是询问生物学概念、生信知识、技术原理（如纳米孔、DNA、测序原理），返回 'answer'；\n"
        f"- 只有当用户在闲聊、骂人或说与科学完全无关的话时，才返回 'irrelevant'。\n"
        f"注意：只返回单词本身，不要任何标点。\n"
        f"用户输入: {user_input}"
    )

    import re
    raw = classification if isinstance(classification, str) else classification.content
    clean_intent = re.sub(r"[^a-z]", "", raw.strip().lower())

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


