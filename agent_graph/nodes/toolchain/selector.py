from agent_graph.nodes.toolchain.single_tool import (
    fallback_single_tool_candidates,
    resolve_single_tool_request,
)
from agent_graph.prompts.toolchain_prompts import build_tools_selector_prompt
from agent_graph.state import AgentState
from configs import TOOL_DESCIPTION, TOOLS_DOC
from utils.lang_utils import get_lang
from utils.llm_utils import get_llm_instance, invoke_json
from utils.nodes_utils import format_history
from utils.ui_logger import ui_print


def select_tools_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    user_feedback = state.get("user_feedback", "")
    history_str = format_history(state.get("chat_history", []))
    tool_sequence = state.get("tool_sequence", [])
    lower_input = (user_input or "").lower()

    if state.get("user_choice") == "workflow":
        ui_print("\n[Tools Selector] Pipeline mode selected by user, skipping tool identification")
        state["identified_tools"] = ["workflow"]
        if not state.get("selected_workflow"):
            state["workflow_type"] = ""
        state["workflow_candidates"] = []
        return state

    if state.get("user_choice") == "tools":
        explicit_tool = resolve_single_tool_request(user_input)
        if explicit_tool:
            ui_print(f"\n[Tools Selector] Tool mode selected - resolved explicit {explicit_tool} request")
            state["identified_tools"] = [explicit_tool]
            state["workflow_type"] = ""
            state["selected_workflow"] = ""
            state["workflow_candidates"] = []
            return state

    ui_print("\n[Tools Selector] Identifying tools for the task...")
    tools_info = "\n".join(f"- {t['name']}: {t['description']}" for t in TOOL_DESCIPTION)
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

        if not valid_tools:
            valid_tools.extend(fallback_single_tool_candidates(user_input))
            if any(
                keyword in lower_input
                for keyword in [
                    "nextflow",
                    "nf-core",
                    "workflow",
                    "pipeline",
                    "methylong",
                    "fiber-seq",
                    "fiberseq",
                    "fiber seq",
                    "nucleosome",
                    "6ma",
                    "m6a",
                    "pacbio",
                    "hifi",
                ]
            ):
                valid_tools.append("workflow")

        ordered = list(dict.fromkeys(valid_tools))
        state["identified_tools"] = ordered[:1]

        is_workflow_request = bool(state["identified_tools"]) and state["identified_tools"][0] == "workflow"
        if is_workflow_request:
            if not state.get("selected_workflow"):
                state["workflow_type"] = ""
            state["workflow_candidates"] = []
        else:
            if state.get("workflow_type"):
                state["workflow_type"] = ""
                state["selected_workflow"] = ""
                state["local_prereq_params"] = {}
                state["nfcore_prereq_params"] = {}

        ui_print(f"[Tools Selector] Identified tools: {state['identified_tools']}")
        ui_print(f"[Tools Selector] Reason: {response.get('reason', 'N/A')}")

    except Exception as e:
        ui_print(f"[Tools Selector Error] Parse failed, using fallback: {e}")
        fallback_tools = fallback_single_tool_candidates(user_input)
        if any(
            keyword in lower_input
            for keyword in ["nextflow", "nf-core", "workflow", "pipeline", "methylong", "pacbio", "hifi"]
        ):
            fallback_tools.append("workflow")
        state["identified_tools"] = list(dict.fromkeys(fallback_tools))[:1]
        state["workflow_type"] = ""
        state["selected_workflow"] = ""
        state["local_prereq_params"] = {}
        state["workflow_candidates"] = []

    return state
