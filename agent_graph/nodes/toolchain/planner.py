
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
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def retrieve_tool_docs_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    if not identified_tools:
        ui_print(f"\n[RAG] No tools identified, skipping retrieval.")
        state["rag_suggestion"] = {}
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"Original request: {user_query}\nUser revision: {user_feedback}"

    print(f"\n[RAG] Retrieving docs for toolchain {identified_tools}...")
    rag_llm = get_llm_instance(is_planner=False)
    rag_suggestion_dict = {}
    is_workflow = state.get("is_workflow", False)

    if is_workflow:
        context = ""
        if "workflows" not in RAG_INSTANCES:
            try:
                RAG_INSTANCES["workflows"] = EnhancedMDRAG(WORKFLOWS_DOC, llm=rag_llm, cache_dir=WORKFLOWS_CACHE_DIR)
            except ValueError as e:
                print(f"[RAG] Workflow docs empty or invalid, skipping: {e}")
        if "workflows" in RAG_INSTANCES:
            context = RAG_INSTANCES["workflows"].search(user_query)
        state["rag_suggestion"] = {"workflows": context}
        print(f"[RAG] Workflow mode — pipeline docs retrieved")
    else:
        for tool in identified_tools:
            doc_path = TOOLS_DOC.get(tool)
            if not doc_path:
                print(f"[RAG] Warning: no doc path mapping for tool {tool}, skipping.")
                continue

            if tool not in RAG_INSTANCES:
                print(f"[RAG] Initializing retrieval index for {tool}...")
                RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm, cache_dir=TOOL_CACHE_DIRS.get(tool))

            retriever = RAG_INSTANCES[tool]
            print(f"[RAG] Retrieving parameters for {tool}...")
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
        print(f"\n[Planner] Tool mode — selecting subcommand...")
        tools_args = [TOOL_ARGS.get(t) for t in identified_tools]
        lang = get_lang()
        chain = ChatPromptTemplate.from_template(build_tool_planner_prompt(lang)) | planner_llm | JsonOutputParser()
        try:
            response = chain.invoke({"input": user_input, "history": history_str, "tools_args": tools_args})
            subcmd = response.get("tool")  # 例如 "samtools sort"
            state["tool_sequence"] = [subcmd] if subcmd else []
            print(f"[Planner] Subcommand: {subcmd}")
        except Exception as e:
            print(f"[Planner Error] {e}")
            state["tool_sequence"] = []

    else:
        # ── Workflow：选具体 pipeline ──
        print(f"\n[Planner] Workflow mode — selecting pipeline...")
        workflow_context = state.get("rag_suggestion", {}).get("workflows", "")
        lang = get_lang()
        chain = ChatPromptTemplate.from_template(build_workflow_planner_prompt(lang)) | planner_llm | JsonOutputParser()
        try:
            from configs.workflow_config import SUPPORTED_PIPELINES
            response = chain.invoke({"input": user_input, "history": history_str, "workflow_context": workflow_context})
            pipeline = response.get("pipeline", "").strip().lower()

            if pipeline not in SUPPORTED_PIPELINES:
                print(f"[Planner] LLM returned unsupported pipeline '{pipeline}', falling back to first supported")
                pipeline = SUPPORTED_PIPELINES[0]

            state["tool_sequence"] = [pipeline]
            state["selected_workflow"] = pipeline
            print(f"[Planner] Selected pipeline: {pipeline} — reason: {response.get('reason')}")
        except Exception as e:
            print(f"[Planner Error] {e}")
            state["tool_sequence"] = []
            state["selected_workflow"] = ""

    return state


