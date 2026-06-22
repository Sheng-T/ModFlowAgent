from typing import TypedDict, List, Dict

EMPTY_STATE = {
    "identified_tools": [],
    "tool_calls": [],
    "tool_output": "",
    "rag_suggestion": {},
    "tool_sequence": [],
    "user_approval": False,
    "user_feedback": "",
    "final_answer": "",
    "next_node": "",
    "selected_workflow": "",
    # "nfcore" → nextflow pipeline  |  "local" → per-tool singularity chain  |  "" → not yet resolved
    "workflow_type": "",
    # populated when LLM is ambiguous; each item: {name, display_name, type, description,
    #   recommended_for, reason, recommended}; cleared after user picks
    "workflow_candidates": [],
    "local_prereq_params": {},
    "nfcore_prereq_params": {},
    "user_choice": None,
    "router_hint": "",
    "pending_commands": [],
    "pre_files": [],
    "samplesheet_issues": [],
    "run_dir": "",
    "analysis_images": [],
    "workflow_result_zip": "",
    "selected_modules": [],
    "module_candidates": [],
    "module_confident": True,
    "forced_modules": [],
}


class AgentState(TypedDict):
    """Core state passed between graph nodes."""

    input: str
    user_choice: str | None
    router_hint: str

    identified_tools: List[str]
    tool_calls: List[str]
    tool_output: List[str]
    rag_suggestion: dict
    tool_sequence: List[str]
    user_feedback: str
    final_answer: str
    chat_history: List[Dict[str, str]]
    next_node: str

    # Workflow routing — replaces the old is_workflow / is_local_workflow bool pair
    workflow_type: str          # "nfcore" | "local" | ""
    workflow_candidates: List[Dict]  # non-empty when ambiguous; cleared after selection
    selected_workflow: str
    # Local workflow prereq params (key-value form, not CSV)
    # e.g. {"data_file": "/path/x.pod5", "reference": "", "modification_type": "m6A"}
    local_prereq_params: Dict
    # nfcore pre-params collected before samplesheet generation (method, molecule)
    nfcore_prereq_params: Dict

    pending_commands: List[str]
    pre_files: List[Dict]
    samplesheet_issues: List[Dict]
    run_dir: str
    analysis_images: List[str]
    workflow_result_zip: str

    selected_modules: List[str]
    module_candidates: List[str]
    module_confident: bool
    forced_modules: List[str]
