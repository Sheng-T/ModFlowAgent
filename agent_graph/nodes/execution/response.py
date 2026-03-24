
from agent_graph.state import AgentState
from utils.llm_utils import get_llm_instance

def answer_general_question_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    print(f"\n[LLM Answer] 正在调用 LLM 回答基础问题: {user_input[:20]}...")
    answer_llm = get_llm_instance(is_planner=False)
    try:
        llm_response = answer_llm.invoke(user_input)
        state["final_answer"] = llm_response.strip()
    except Exception as e:
        print(f"LLM 调用失败: {e}")
        state["final_answer"] = "抱歉，LLM 服务暂时不可用，无法回答您的问题。"
    print(f'\n[LLM Answer] {state["final_answer"]}')
    return state


def summarize_execution_result_node(state: AgentState) -> AgentState:
    tool_calls = state.get("tool_calls", [])
    tool_output = state.get("tool_output", [])
    if not tool_calls:
        return state

    print("\n[Summarizer] 正在总结最终答案...")
    output = "\n".join(tool_output)
    summary = f"根据您的需求，已成功执行操作。工具输出结果：{output}. 请查看文件。"
    state["final_answer"] = summary
    print(f'\n[LLM Answer] {state["final_answer"]}')
    return state

def handle_irrelevant_request_node(state: AgentState) -> AgentState:
    print("\n[Irrelevant] 生成不相关回复...")
    state["final_answer"] = "抱歉，我专注于纳米孔测序和修饰检测相关的任务，无法为您提供该信息。"
    print(f'\n[LLM Answer] {state["final_answer"]}')
    return state


def finish_session_node(state: AgentState) -> AgentState:
    print(f"\n[End] 本次会话结束")
    return state

