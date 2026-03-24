
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import (
    build_tool_planner_prompt,
)
from configs import TOOLS_DOC, RAG_INSTANCES, TOOL_ARGS
from storage.rag_retriever import EnhancedMDRAG
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history


def retrieve_tool_docs_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    if not identified_tools:
        print(f"\n[RAG] 未识别到工具，跳过检索流程。")
        state["rag_suggestion"] = {}
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"初始需求: {user_query}\n用户最新追加/修改指令: {user_feedback}"

    print(f"\n[RAG] 正在为工具链 {identified_tools} 检索背景知识...")
    rag_llm = get_llm_instance(is_planner=False)
    rag_suggestion_dict = {}

    for tool in identified_tools:
        doc_path = TOOLS_DOC.get(tool)
        if not doc_path:
            print(f"[RAG] 警告: 未找到工具 {tool} 的文档路径映射，跳过。")
            continue

        if tool not in RAG_INSTANCES:
            print(f"[RAG] 正在初始化 {tool} 的检索索引...")
            RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm)

        retriever = RAG_INSTANCES[tool]
        print(f"[RAG] 正在检索 {tool} 相关参数...")
        context = retriever.search(user_query)
        rag_suggestion_dict[tool.lower()] = context

    state["rag_suggestion"] = rag_suggestion_dict
    return state


def plan_tool_steps_node(state: AgentState) -> AgentState:
    planner_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    identified_tools = state.get("identified_tools", [])
    history_str = format_history(state.get("chat_history", []))

    if not identified_tools:
        return state

    print(f"\n[Planner] 单工具模式，仅选择一个最合适的工具...")
    prompt = ChatPromptTemplate.from_template(build_tool_planner_prompt())

    chain = prompt | planner_llm | JsonOutputParser()
    tools_args = [TOOL_ARGS.get(t.lower()) for t in identified_tools]

    try:
        response = chain.invoke(
            {"input": user_input, "history": history_str, "tools_args": tools_args}
        )
        tool_name = response.get("tool")
        state["tool_sequence"] = [tool_name] if tool_name else []
        print(f"[Planner] 选择工具: {tool_name}")
    except Exception as e:
        print(f"[Planner Error] {e}")
        state["tool_sequence"] = []

    return state


