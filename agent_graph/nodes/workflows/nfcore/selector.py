
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent_graph.prompts.nfcore_prompts import (
    build_nfcore_selector_prompt,
)
from agent_graph.state import AgentState
from utils.llm_utils import get_llm_instance

def select_nfcore_pipeline_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    user_input_lower = user_input.lower()
    if any(k in user_input_lower for k in ["methylong", "甲基化", "modbam", "pod5", "pacbio", "ont"]):
        state["tool_sequence"] = ["nextflow_methylong"]
        state["identified_tools"] = ["nextflow"]
        state["workflow_candidate"] = "methylong"
        return state

    llm = get_llm_instance(is_planner=True)
    prompt = ChatPromptTemplate.from_template(build_nfcore_selector_prompt())
    chain = prompt | llm | JsonOutputParser()

    try:
        resp = chain.invoke({"user_input": user_input})
        pipeline = resp.get("pipeline", "custom")
        state["tool_sequence"] = [f"nextflow_{pipeline}"]
        state["identified_tools"] = ["nextflow"]
        state["workflow_candidate"] = pipeline
    except Exception:
        state["tool_sequence"] = ["nextflow_custom"]
        state["identified_tools"] = ["nextflow"]
        state["workflow_candidate"] = "custom"
    return state

def confirm_nfcore_workflow_node(state: AgentState) -> AgentState:
    candidate = state.get("workflow_candidate", "custom")
    print(f"\n[NFCore] 自动选择的 workflow: {candidate}")
    print("[NFCore] 是否确认该 workflow？(y=确认, n=重新自动选择, 或直接输入 workflow 名称覆盖)")
    user_choice = input("[NFCore] 请输入 y/n/workflow: ").strip().lower()

    if user_choice == "y" or user_choice == "":
        state["selected_workflow"] = candidate
        state["next_node"] = "nfcore_rag"
        return state

    if user_choice == "n":
        state["next_node"] = "nfcore_selector"
        return state

    # custom manual override
    state["selected_workflow"] = user_choice
    state["tool_sequence"] = [f"nextflow_{user_choice}"]
    state["workflow_candidate"] = user_choice
    state["next_node"] = "nfcore_rag"
    return state

