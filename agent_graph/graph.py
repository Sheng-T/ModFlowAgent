from langgraph.graph import END, StateGraph
from agent_graph.nodes import (
    answer_general_question_node,
    classify_intent_route,
    execute_commands_node,
    finish_session_node,
    generate_local_prereqs_node,
    generate_tool_params_node,
    handle_irrelevant_request_node,
    human_local_prereq_reviewer_node,
    human_module_selector_node,
    human_workflow_selector_node,
    plan_tool_steps_node,
    reset_session_state_node,
    retrieve_tool_docs_node,
    review_execution_plan_node,
    select_analysis_modules_node,
    select_tools_node,
    summarize_execution_result_node,
)
from agent_graph.nodes.workflows.planner import retrieve_pipeline_docs_node
from agent_graph.nodes.workflows.prereq import generate_prereqs_node, human_prereq_reviewer_node
from utils.workflow_prerequisites import needs_prereq, needs_local_prereq
from agent_graph.state import AgentState


from configs.app_config import APP_SNAKE

def save_graph_image(app_instance, filename=None):
    if filename is None:
        filename = f"{APP_SNAKE}_graph.txt"
    try:
        mermaid_code = app_instance.get_graph().draw_mermaid()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(mermaid_code)
        print(f"\n[System] 流程图已保存至本地: {filename}")
    except Exception as e:
        print(f"\n[System] 保存失败: {e}")


def create_agent_graph(agent_name: str, is_save_graph_image: bool = False, graph_image_filename: str = "") -> StateGraph:
    workflow = StateGraph(AgentState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    workflow.add_node("router",                       reset_session_state_node)
    workflow.add_node("tools_selector",               select_tools_node)
    workflow.add_node("rag",                          retrieve_tool_docs_node)
    workflow.add_node("planner",                      plan_tool_steps_node)
    # Workflow type disambiguation (shown when LLM cannot auto-select)
    workflow.add_node("human_workflow_selector",      human_workflow_selector_node)
    # nfcore: detailed pipeline docs → CSV samplesheet prereq
    workflow.add_node("rag_pipeline",                 retrieve_pipeline_docs_node)
    workflow.add_node("prereq_generator",             generate_prereqs_node)
    workflow.add_node("human_prereq_reviewer",        human_prereq_reviewer_node)
    # local: key-value param form prereq
    workflow.add_node("local_prereq_generator",       generate_local_prereqs_node)
    workflow.add_node("human_local_prereq_reviewer",  human_local_prereq_reviewer_node)
    workflow.add_node("param_generator",              generate_tool_params_node)
    workflow.add_node("human_reviewer",               review_execution_plan_node)
    workflow.add_node("executor",                     execute_commands_node)
    workflow.add_node("module_selector",              select_analysis_modules_node)
    workflow.add_node("human_module_selector",        human_module_selector_node)
    workflow.add_node("summarizer",                   summarize_execution_result_node)
    workflow.add_node("llm_answer",                   answer_general_question_node)
    workflow.add_node("irrelevant",                   handle_irrelevant_request_node)
    workflow.add_node("end_node",                     finish_session_node)

    # ── Entry ──────────────────────────────────────────────────────────────────
    workflow.set_entry_point("router")

    # ── Router ─────────────────────────────────────────────────────────────────
    workflow.add_conditional_edges(
        "router",
        lambda state: classify_intent_route(state),
        {
            "route_to_tools":      "tools_selector",
            "route_to_answer":     "llm_answer",
            "route_to_irrelevant": "irrelevant",
        }
    )

    # ── Core pipeline ──────────────────────────────────────────────────────────
    workflow.add_edge("tools_selector", "rag")
    workflow.add_edge("rag",            "planner")

    # ── Planner routing ────────────────────────────────────────────────────────
    # Priorities:
    #   1. workflow_candidates set  → user must pick workflow first
    #   2. nfcore + tool_sequence   → fetch detailed pipeline docs
    #   3. local + tool_sequence + needs_local_prereq + no params yet
    #                               → local param form
    #   4. tool_sequence set        → generate parameters (single tool or local after prereq)
    #   5. nothing                  → summarize (no-op path)
    def _planner_route(state):
        wt  = state.get("workflow_type", "")
        seq = state.get("tool_sequence", [])
        wf  = state.get("selected_workflow", "")
        if state.get("workflow_candidates"):
            return "ask_workflow"
        if wt == "nfcore" and seq:
            return "fetch_pipeline_doc"
        if wt == "local" and seq and needs_local_prereq(wf):
            return "local_prereq"
        if seq:
            return "generate_parameters"
        return "route_to_summarize"

    workflow.add_conditional_edges(
        "planner",
        _planner_route,
        {
            "ask_workflow":        "human_workflow_selector",
            "fetch_pipeline_doc":  "rag_pipeline",
            "local_prereq":        "local_prereq_generator",
            "generate_parameters": "param_generator",
            "route_to_summarize":  "summarizer",
        }
    )

    # After user picks a workflow, loop back to planner to resolve tool_sequence
    workflow.add_edge("human_workflow_selector", "planner")

    # ── nfcore prereq flow ─────────────────────────────────────────────────────
    workflow.add_conditional_edges(
        "rag_pipeline",
        lambda state: "prereq_generator" if needs_prereq(state.get("selected_workflow", "")) else "param_generator",
        {
            "prereq_generator": "prereq_generator",
            "param_generator":  "param_generator",
        }
    )
    workflow.add_edge("prereq_generator",      "human_prereq_reviewer")
    workflow.add_edge("human_prereq_reviewer", "param_generator")

    # ── local workflow prereq flow ─────────────────────────────────────────────
    workflow.add_edge("local_prereq_generator",      "human_local_prereq_reviewer")
    workflow.add_edge("human_local_prereq_reviewer", "param_generator")

    # ── Execution flow ─────────────────────────────────────────────────────────
    workflow.add_edge("param_generator", "human_reviewer")

    workflow.add_conditional_edges(
        "human_reviewer",
        lambda state: state.get("next_node") or "param_generator",
        {
            "tools_selector":  "tools_selector",
            "executor":        "executor",
            "rag":             "rag",
            "param_generator": "param_generator",
            "end_node":        "end_node",
        }
    )

    workflow.add_conditional_edges(
        "executor",
        lambda state: state.get("next_node") or "module_selector",
        {
            "param_generator": "param_generator",
            "module_selector": "module_selector",
            "summarizer":      "summarizer",
            "tools_selector":  "tools_selector",
        }
    )

    workflow.add_conditional_edges(
        "module_selector",
        lambda state: "summarizer" if state.get("module_confident", True) else "human_module_selector",
        {
            "summarizer":            "summarizer",
            "human_module_selector": "human_module_selector",
        }
    )

    workflow.add_edge("human_module_selector", "summarizer")
    workflow.add_edge("llm_answer",  END)
    workflow.add_edge("summarizer",  END)
    workflow.add_edge("irrelevant",  END)
    workflow.add_edge("end_node",    END)

    # ── Compile ────────────────────────────────────────────────────────────────
    from storage.checkpointer import get_checkpointer
    checkpointer = get_checkpointer()
    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "human_workflow_selector",        # user picks workflow type
            "human_local_prereq_reviewer",    # user confirms local prereq params
            "human_module_selector",
            "human_prereq_reviewer",
        ],
        interrupt_after=[
            "human_reviewer",                 # user reviews pending commands before executor runs
        ],
    )
    app.name = agent_name
    if is_save_graph_image:
        save_graph_image(app, graph_image_filename)
    return app
