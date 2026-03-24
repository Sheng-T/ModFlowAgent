

from agent_graph.state import AgentState
from tools.workflow.validator import validate_nfcore_kwargs


def validate_nfcore_params_node(state: AgentState) -> AgentState:
    tool_calls = state.get("tool_calls", [])
    if not tool_calls:
        return state

    call = tool_calls[0]
    kwargs = call.get("tool_args", {}).get("kwargs", {})
    err = validate_nfcore_kwargs(kwargs)
    if err:
        state.setdefault("chat_history", []).append({"role": "assistant", "content": err})
        state["next_node"] = "nfcore_param_generator"
    else:
        state["next_node"] = "human_reviewer"
    return state

