from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import build_tools_selector_prompt
from configs import TOOL_DESCIPTION, TOOLS_DOC

from utils.llm_utils import get_llm_instance, invoke_json
from utils.nodes_utils import format_history
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def select_tools_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    user_feedback = state.get("user_feedback", "")
    history_str = format_history(state.get("chat_history", []))
    tool_sequence = state.get("tool_sequence", [])

    # User explicitly chose "workflow" mode from the UI — skip LLM, go straight to planner
    if state.get("user_choice") == "workflow":
        ui_print(f"\n[Tools Selector] Pipeline mode selected by user, skipping tool identification")
        state["identified_tools"] = ["workflow"]
        if not state.get("selected_workflow"):
            state["workflow_type"] = ""   # not yet resolved; planner will pick
        state["workflow_candidates"] = []
        return state

    ui_print(f"\n[Tools Selector] Identifying tools for the task...")
    tools_info = "\n".join([f"- {t['name']}: {t['description']}" for t in TOOL_DESCIPTION])
    selector_llm = get_llm_instance(is_planner=True)
    prompt_str = build_tools_selector_prompt(get_lang()).format(
        input=user_input,
        tools_info=tools_info,
        history=history_str,
        tool_sequence=tool_sequence,
        user_feedback=user_feedback,
    )
    try:
        response = invoke_json(selector_llm, prompt_str)
        selected = response.get("selected_tools", [])
        valid_tools = [t for t in selected if t in TOOLS_DOC.keys() or t == "workflow"]

        # keyword fallback
        if not valid_tools:
            lower = user_input.lower()
            if "basecall" in lower or "dorado" in lower:
                valid_tools.append("dorado")
            if "sort" in lower or "index" in lower:
                valid_tools.append("samtools")
            if any(k in lower for k in ["nextflow", "nf-core", "workflow", "pipeline", "流水线", "流程",
                                         "methylong", "fiber-seq", "fiberseq", "fiber seq",
                                         "nucleosome", "核小体", "6ma", "m6a", "pacbio", "hifi"]):
                valid_tools.append("workflow")

        ordered = list(dict.fromkeys(valid_tools))
        state["identified_tools"] = ordered[:1]

        is_workflow_request = (
            len(state["identified_tools"]) > 0
            and state["identified_tools"][0] == "workflow"
        )
        if is_workflow_request:
            # Preserve resolved workflow_type when same workflow is continuing;
            # clear only on first run (no selected_workflow) so planner can resolve it.
            if not state.get("selected_workflow"):
                state["workflow_type"] = ""
            state["workflow_candidates"] = []
        else:
            # User switched away from workflow mode — clear workflow state
            if state.get("workflow_type"):
                state["workflow_type"] = ""
                state["selected_workflow"] = ""
                state["local_prereq_params"] = {}
                state["nfcore_prereq_params"] = {}

        ui_print(f"[Tools Selector] Identified tools: {state['identified_tools']}")
        ui_print(f"[Tools Selector] Reason: {response.get('reason', 'N/A')}")

    except Exception as e:
        ui_print(f"[Tools Selector Error] Parse failed, using fallback: {e}")
        state["identified_tools"] = []
        state["workflow_type"] = ""
        state["selected_workflow"] = ""
        state["local_prereq_params"] = {}
        state["workflow_candidates"] = []

    return state
