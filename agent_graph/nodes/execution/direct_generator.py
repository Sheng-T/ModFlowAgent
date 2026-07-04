"""One-step workflow plan generator -- bypasses staged controller for ablation."""
from agent_graph.state import AgentState
import tools.workflow.registry as wf_registry
from utils.llm_utils import get_llm_instance
from utils.ui_logger import ui_print


def direct_generate_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    history = list(state.get("chat_history", []))

    specs = wf_registry.all_specs()
    workflow_list = "\n".join([
        f"- {s.name}: {s.display_name} ({s.type})"
        for s in specs
    ])

    llm = get_llm_instance(is_planner=True)

    prompt = (
        f"You are a bioinformatics workflow assistant.\n\n"
        f"Available workflows:\n{workflow_list}\n\n"
        f"User request:\n{user_input}\n\n"
        f"Generate the best response in one step. "
        f"If the request is ambiguous or lacks required information, ask concise clarification questions. "
        f"If the request is invalid or unsupported, explain why and do not generate executable commands. "
        f"Otherwise, provide the selected workflow, required inputs, key parameters, "
        f"and commands that would be executed.\n\n"
        f"Return your answer in a clear structured format."
    )

    ui_print("[DirectGenerator] Generating one-step workflow plan...")
    raw = llm.invoke(prompt)
    response = raw if isinstance(raw, str) else raw.content

    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": response})

    return {"final_answer": response, "chat_history": history}
