
import os
from agent_graph.state import AgentState
from configs import WORKFLOW_PIPELINE_DOCS, RAG_INSTANCES, WORKFLOW_CACHE_DIRS
from storage.rag_retriever import EnhancedMDRAG
from utils.llm_utils import get_llm_instance

def retrieve_pipeline_docs_node(state: AgentState) -> AgentState:
    pipeline = state.get("selected_workflow")
    if not pipeline:
        print("[RAG Pipeline] No selected_workflow found, skipping")
        return state
    if os.environ.get("ABLATION_NO_RAG", "0") == "1":
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"Original request: {user_query}\nUser follow-up: {user_feedback}"

    doc_path = WORKFLOW_PIPELINE_DOCS.get(pipeline)
    if not doc_path:
        print(f"[RAG Pipeline] Warning: no docs found for {pipeline}, skipping")
        return state

    print(f"\n[RAG Pipeline] Retrieving parameter docs for {pipeline}...")
    rag_llm = get_llm_instance(is_planner=False)

    cache_key = f"pipeline_{pipeline}"
    if cache_key not in RAG_INSTANCES:
        RAG_INSTANCES[cache_key] = EnhancedMDRAG(doc_path, llm=rag_llm, cache_dir=WORKFLOW_CACHE_DIRS.get(pipeline), )

    context = RAG_INSTANCES[cache_key].search(user_query)

    # 写入 rag_suggestion，key 用 pipeline 名，param_generator 直接取
    state["rag_suggestion"][pipeline] = context
    print(f"[RAG Pipeline] {pipeline} docs retrieved")
    return state

