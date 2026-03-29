
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent_graph.prompts.workflow_prompts import build_workflow_planner_prompt
from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import (
    build_tool_planner_prompt,
)
from configs import TOOLS_DOC, RAG_INSTANCES, TOOL_ARGS, WORKFLOWS_DOC, WORKFLOWS_CACHE_DIR, TOOL_CACHE_DIRS
from storage.rag_retriever import EnhancedMDRAG
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history

# 多层级导入保证兼容性
try:
    from utils.ui_logger import ui_print
except ImportError:
    try:
        from ....utils.ui_logger import ui_print
    except ImportError:
        ui_print = print


def retrieve_tool_docs_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    if not identified_tools:
        ui_print(f"\n[RAG] 未识别到工具，跳过检索流程。")
        state["rag_suggestion"] = {}
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"初始需求: {user_query}\n用户最新追加/修改指令: {user_feedback}"

    print(f"\n[RAG] 正在为工具链 {identified_tools} 检索背景知识...")
    rag_llm = get_llm_instance(is_planner=False)
    rag_suggestion_dict = {}
    is_workflow = state.get("is_workflow", False)

    if is_workflow:
        if "workflows" not in RAG_INSTANCES:
            RAG_INSTANCES["workflows"] = EnhancedMDRAG(WORKFLOWS_DOC, llm=rag_llm, cache_dir=WORKFLOWS_CACHE_DIR,)
        context = RAG_INSTANCES["workflows"].search(user_query)
        state["rag_suggestion"] = {"workflows": context}
        print(f"[RAG] Workflow 模式，检索 pipeline 目录完成")
    else:
        for tool in identified_tools:
            doc_path = TOOLS_DOC.get(tool)
            if not doc_path:
                print(f"[RAG] 警告: 未找到工具 {tool} 的文档路径映射，跳过。")
                continue

            if tool not in RAG_INSTANCES:
                print(f"[RAG] 正在初始化 {tool} 的检索索引...")
                RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm, cache_dir=TOOL_CACHE_DIRS.get(tool))

            retriever = RAG_INSTANCES[tool]
            print(f"[RAG] 正在检索 {tool} 相关参数...")
            context = retriever.search(user_query)
            rag_suggestion_dict[tool.lower()] = context

    state["rag_suggestion"] = rag_suggestion_dict
    return state


def plan_tool_steps_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    is_workflow = state.get("is_workflow", False)
    if not identified_tools:
        return state

    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    planner_llm = get_llm_instance(is_planner=True)

    if not is_workflow:
        # ── 普通工具：选子命令 ──
        print(f"\n[Planner] 工具模式，选择子命令...")
        tools_args = [TOOL_ARGS.get(t) for t in identified_tools]
        chain = ChatPromptTemplate.from_template(build_tool_planner_prompt()) | planner_llm | JsonOutputParser()
        try:
            response = chain.invoke({"input": user_input, "history": history_str, "tools_args": tools_args})
            subcmd = response.get("tool")  # 例如 "samtools sort"
            state["tool_sequence"] = [subcmd] if subcmd else []
            print(f"[Planner] 子命令: {subcmd}")
        except Exception as e:
            print(f"[Planner Error] {e}")
            state["tool_sequence"] = []

    else:
        # ── Workflow：选具体 pipeline ──
        print(f"\n[Planner] Workflow 模式，选择具体 pipeline...")
        workflow_context = state.get("rag_suggestion", {}).get("workflows", "")
        chain = ChatPromptTemplate.from_template(build_workflow_planner_prompt()) | planner_llm | JsonOutputParser()
        try:
            response = chain.invoke({"input": user_input, "history": history_str, "workflow_context": workflow_context})
            pipeline = response.get("pipeline")  # 例如 "rnaseq"
            state["tool_sequence"] = [pipeline] if pipeline else []
            state["selected_workflow"] = pipeline  # param_generator 用这个找 args
            print(f"[Planner] 选中 pipeline: {pipeline}，理由: {response.get('reason')}")
        except Exception as e:
            print(f"[Planner Error] {e}")
            state["tool_sequence"] = []
            state["selected_workflow"] = ""

    return state


