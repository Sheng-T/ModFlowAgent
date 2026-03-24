
import json
import re


from agent_graph.prompts.nfcore_prompts import (
    build_nfcore_param_prompt,
    build_nfcore_selector_prompt,
)
from agent_graph.state import AgentState
from configs import TOOLS_DOC
from configs.workflow_config import DEFAULT_NFCORE_ARGS
from storage.rag_retriever import EnhancedMDRAG
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history

def retrieve_nfcore_docs_node(state: AgentState) -> AgentState:
    global NFCORE_RAG_INSTANCE
    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"初始需求: {user_query}\n用户最新追加/修改指令: {user_feedback}"

    doc_path = TOOLS_DOC.get("nextflow")
    if not doc_path:
        state["rag_suggestion"] = {"nextflow": "No nf-core doc configured."}
        return state

    rag_llm = get_llm_instance(is_planner=False)
    if NFCORE_RAG_INSTANCE is None:
        NFCORE_RAG_INSTANCE = EnhancedMDRAG(doc_path, llm=rag_llm)
    state["rag_suggestion"] = {"nextflow": NFCORE_RAG_INSTANCE.search(user_query)}
    return state


def generate_nfcore_params_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    rag_text = state.get("rag_suggestion", {}).get("nextflow", "")
    current_seq = state.get("tool_sequence", ["nextflow_custom"])[0]
    pipeline = state.get("selected_workflow", "")
    if not pipeline:
        pipeline = current_seq.replace("nextflow_", "") if current_seq.startswith("nextflow_") else "custom"

    llm = get_llm_instance(is_planner=True)
    base_prompt = build_nfcore_param_prompt()
    prompt = (
        f"{base_prompt}\n"
        f"\n用户需求: {user_input}\n"
        f"历史: {history_str}\n"
        f"检索文档: {rag_text}\n"
        f"预选 pipeline: {pipeline}\n"
    )

    try:
        raw = llm.invoke(prompt)
        content = raw if isinstance(raw, str) else raw.content
        clean = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        call = json.loads(clean)
        kwargs = call.setdefault("tool_args", {}).setdefault("kwargs", {})
        for k, v in DEFAULT_NFCORE_ARGS.items():
            kwargs.setdefault(k, v)
    except Exception:
        call = {
            "tool_name": "nextflow_run_nfcore",
            "tool_args": {
                "pos_args": [],
                "kwargs": {
                    "pipeline": pipeline if pipeline != "custom" else "rnaseq",
                    "input": "samplesheet.csv",
                    "outdir": "nfcore_out",
                    **DEFAULT_NFCORE_ARGS,
                },
            },
        }

    state["tool_calls"] = [call]
    return state

