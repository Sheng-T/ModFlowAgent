"""
Workflow selection interrupt node.

The graph interrupts *before* this node so the UI can read
state["workflow_candidates"] and present them to the user.
After the user picks one, state["selected_workflow"] is set by the resume
mechanism and this node resolves workflow_type from the registry, then
clears workflow_candidates so the next planner pass can proceed.
"""
import tools.workflow.registry as wf_registry
from agent_graph.state import AgentState
from utils.ui_logger import ui_print


def human_workflow_selector_node(state: AgentState) -> dict:
    chosen = state.get("selected_workflow", "")
    if not chosen:
        ui_print("[Workflow Selector] No workflow chosen yet, keeping candidates.")
        return {}

    spec = wf_registry.get(chosen)
    if not spec:
        ui_print(f"[Workflow Selector] Unknown workflow '{chosen}', clearing candidates.")
        return {"workflow_candidates": []}

    ui_print(f"[Workflow Selector] User selected: {spec.display_name}  (type: {spec.type})")
    return {
        "workflow_type": spec.type,
        "workflow_candidates": [],
        "user_confirmed_workflow": True,
    }
