import re as _re

from agent_graph.prompts.workflow_prompts import build_workflow_planner_prompt
from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import build_tool_planner_prompt
from configs import TOOLS_DOC, RAG_INSTANCES, TOOL_ARGS, TOOL_CACHE_DIRS
from configs.rag_config import WORKFLOW_PIPELINE_DOCS, WORKFLOW_CACHE_DIRS
from storage.rag_retriever import EnhancedMDRAG
import tools.workflow.registry as wf_registry
from utils.llm_utils import get_llm_instance, invoke_json
from utils.nodes_utils import format_history
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


# ── Helpers ────────────────────────────────────────────────────────────────────

def _format_workflow_list(specs: list, lang: str) -> str:
    """Format all registered workflow specs into a human-readable block for the LLM prompt."""
    lines = []
    for s in specs:
        if lang == "en_US":
            lines.append(
                f"- {s.name}  ({s.display_name})  [type: {s.type}]\n"
                f"  Description: {s.description}\n"
                f"  Best for: {s.recommended_for}\n"
                f"  Molecule: {s.molecule or 'N/A'}  |  "
                f"Modification: {s.modification or 'N/A'}  |  "
                f"Input: {', '.join(s.input_formats) or 'any'}"
            )
        else:
            lines.append(
                f"- {s.name}  ({s.display_name})  [类型: {s.type}]\n"
                f"  说明: {s.description}\n"
                f"  适用场景: {s.recommended_for}\n"
                f"  分子: {s.molecule or '通用'}  |  "
                f"修饰: {s.modification or '通用'}  |  "
                f"输入: {', '.join(s.input_formats) or '任意'}"
            )
    return "\n\n".join(lines)


def _fetch_local_tool_docs(state: AgentState, spec) -> None:
    """Fetch per-tool RAG docs for a local workflow's step tools into state['rag_suggestion']."""
    user_query = state.get("input", "")
    rag_llm = get_llm_instance(is_planner=False)
    rag_dict = state.get("rag_suggestion", {})

    unique_tools = list(dict.fromkeys(spec.step_tools))
    for tool in unique_tools:
        if tool in rag_dict:
            continue
        doc_path = TOOLS_DOC.get(tool)
        if not doc_path:
            ui_print(f"[Planner] No doc path for '{tool}', skipping RAG.")
            continue
        if tool not in RAG_INSTANCES:
            RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm, cache_dir=TOOL_CACHE_DIRS.get(tool))
        rag_dict[tool] = RAG_INSTANCES[tool].search(user_query)

    state["rag_suggestion"] = rag_dict


# ── RAG node ───────────────────────────────────────────────────────────────────

def retrieve_tool_docs_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    if not identified_tools:
        ui_print(f"\n[RAG] No tools identified, skipping retrieval.")
        state["rag_suggestion"] = {}
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")
    if user_feedback:
        user_query = f"Original request: {user_query}\nUser revision: {user_feedback}"

    is_workflow_request = identified_tools == ["workflow"]
    workflow_type = state.get("workflow_type", "")

    if is_workflow_request and workflow_type == "":
        # Workflow type not yet resolved — planner will handle selection.
        # Optionally fetch nfcore pipeline overview docs as broad context.
        ui_print(f"\n[RAG] Workflow request (type not yet resolved) — fetching pipeline overview docs...")
        rag_llm = get_llm_instance(is_planner=False)
        context_parts = []
        for wf_name, doc_path in WORKFLOW_PIPELINE_DOCS.items():
            key = f"workflow_{wf_name}"
            if key not in RAG_INSTANCES:
                try:
                    RAG_INSTANCES[key] = EnhancedMDRAG(
                        doc_path, llm=rag_llm, cache_dir=WORKFLOW_CACHE_DIRS.get(wf_name)
                    )
                except ValueError as e:
                    ui_print(f"[RAG] {wf_name} docs empty or invalid, skipping: {e}")
                    continue
            ctx = RAG_INSTANCES[key].search(user_query)
            if ctx:
                context_parts.append(f"[{wf_name}]\n{ctx}")
        state["rag_suggestion"] = {"workflows": "\n\n".join(context_parts)}

    elif workflow_type == "local" and state.get("selected_workflow"):
        # Local workflow already resolved (re-entry after human_workflow_selector)
        spec = wf_registry.get(state["selected_workflow"])
        if spec:
            ui_print(f"\n[RAG] Local workflow '{spec.name}' — fetching per-tool docs...")
            _fetch_local_tool_docs(state, spec)

    elif workflow_type == "nfcore":
        # nfcore: rag_pipeline node handles the specific pipeline docs — nothing to do here
        ui_print(f"\n[RAG] nfcore workflow — pipeline docs handled by rag_pipeline node.")

    else:
        # Single tool
        rag_llm = get_llm_instance(is_planner=False)
        rag_suggestion_dict = {}
        ui_print(f"\n[RAG] Retrieving docs for tools: {identified_tools}...")
        for tool in identified_tools:
            doc_path = TOOLS_DOC.get(tool)
            if not doc_path:
                ui_print(f"[RAG] Warning: no doc path for '{tool}', skipping.")
                continue
            if tool not in RAG_INSTANCES:
                ui_print(f"[RAG] Initializing retrieval index for {tool}...")
                RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm, cache_dir=TOOL_CACHE_DIRS.get(tool))
            ui_print(f"[RAG] Retrieving parameters for {tool}...")
            rag_suggestion_dict[tool.lower()] = RAG_INSTANCES[tool].search(user_query)
        state["rag_suggestion"] = rag_suggestion_dict

    return state


# ── Planner node ───────────────────────────────────────────────────────────────

def plan_tool_steps_node(state: AgentState) -> AgentState:
    identified_tools = state.get("identified_tools", [])
    if not identified_tools:
        return state

    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    planner_llm = get_llm_instance(is_planner=True)
    lang = get_lang()

    is_workflow_request = identified_tools == ["workflow"]
    workflow_type = state.get("workflow_type", "")
    selected_workflow = state.get("selected_workflow", "")

    # ── Workflow branch ────────────────────────────────────────────────────────
    if is_workflow_request or workflow_type in ("nfcore", "local"):

        # Case A: already resolved (auto-selected or user picked via human_workflow_selector)
        if selected_workflow and not state.get("workflow_candidates"):
            # Switch-detection: collect distinguishing signals from OTHER workflows
            # (name, display-name words, molecule type) and check against user input.
            user_lower = user_input.lower()
            _SKIP_WORDS = {"local", "nf-core", "nfcore", "modification", "analysis",
                           "workflow", "pipeline", "(local)", "(nf-core)",
                           "ont", "sequencing", "data", "file", "input"}
            switch_signals: set[str] = set()
            current_spec = wf_registry.get(selected_workflow)
            for s in wf_registry.all_specs():
                if s.name.lower() == selected_workflow.lower():
                    continue
                switch_signals.add(s.name.lower())
                for w in s.display_name.lower().split():
                    w = w.strip("()")
                    if w not in _SKIP_WORDS and len(w) > 1:
                        switch_signals.add(w)
                if s.molecule:
                    switch_signals.add(s.molecule.lower())
            # Remove signals that also appear in the CURRENT workflow to avoid false positives
            if current_spec:
                current_signals: set[str] = {current_spec.name.lower()}
                for w in current_spec.display_name.lower().split():
                    w = w.strip("()")
                    if w not in _SKIP_WORDS and len(w) > 1:
                        current_signals.add(w)
                if current_spec.molecule:
                    current_signals.add(current_spec.molecule.lower())
                switch_signals -= current_signals
            def _is_switch_keyword(text: str, sig: str) -> bool:
                """True only when sig appears as a standalone intent, not inside X/sig or sig/X."""
                pattern = _re.escape(sig)
                for m in _re.finditer(pattern, text):
                    s, e = m.start(), m.end()
                    before = text[s - 1] if s > 0 else " "
                    after  = text[e]     if e < len(text) else " "
                    # Skip: part of a longer word or a slash-compound (e.g. "dna/rna")
                    if before in "/\\-" or after in "/\\-":
                        continue
                    if before.isalnum() or after.isalnum():
                        continue
                    return True
                return False

            keyword_hit = any(_is_switch_keyword(user_lower, sig) for sig in switch_signals)

            if keyword_hit:
                ui_print("[Planner] Switch keyword detected — re-selecting via LLM.")
                state["selected_workflow"] = ""
                state["workflow_type"] = ""
                state["local_prereq_params"] = {}
                state["nfcore_prereq_params"] = {}
                # fall through to Case B below

            elif current_spec:
                # No keyword switch signal — trust the already-selected workflow and fast-path.
                # LLM re-verification is intentionally skipped here: it was causing an infinite
                # loop where vague inputs returned confident=false and re-queued candidates even
                # after the user had explicitly chosen a workflow.
                spec = wf_registry.get(selected_workflow)
                if spec:
                    _prev = (state.get("local_prereq_params") or {}).get("_workflow", "")
                    if _prev and _prev != spec.name:
                        state["local_prereq_params"] = {}
                        state["nfcore_prereq_params"] = {}
                    state["workflow_type"] = spec.type
                    state["tool_sequence"] = ([spec.name] if spec.type == "nfcore"
                                              else list(spec.steps))
                    if spec.type == "local":
                        _fetch_local_tool_docs(state, spec)
                    state["workflow_candidates"] = []
                    ui_print(f"[Planner] '{spec.display_name}' (no switch detected) → steps: {state['tool_sequence']}")
                else:
                    state["tool_sequence"] = []
                    state["workflow_type"] = ""
                return state

            else:
                # No current spec found — fall through to Case B
                state["selected_workflow"] = ""
                state["workflow_type"] = ""

        # Case B: not yet resolved → use LLM to select
        ui_print(f"\n[Planner] Workflow mode — selecting from registry with LLM...")
        all_specs = wf_registry.all_specs()
        workflow_list = _format_workflow_list(all_specs, lang)
        valid_names = wf_registry.all_names()

        prompt_str = build_workflow_planner_prompt(lang).format(
            input=user_input,
            history=history_str,
            workflow_list=workflow_list,
        )
        try:
            response = invoke_json(planner_llm, prompt_str)
            chosen = (response.get("workflow") or "").strip().lower()
            confident = bool(response.get("confident", False))
            candidates_raw = response.get("candidates", [])

            if confident and chosen in valid_names:
                # Auto-select — no need to interrupt the user
                spec = wf_registry.get(chosen)
                # Clear stale prereq params when switching to a different workflow.
                # Compare against local_prereq_params._workflow (not selected_workflow,
                # which is cleared by entry.py on every new turn).
                _prev_wf = (state.get("local_prereq_params") or {}).get("_workflow", "")
                if spec.name != _prev_wf:
                    state["local_prereq_params"] = {}
                    state["nfcore_prereq_params"] = {}
                    ui_print(f"[Planner] Workflow changed → cleared local/nfcore prereq params")
                state["selected_workflow"] = spec.name
                state["workflow_type"] = spec.type
                state["tool_sequence"] = [spec.name] if spec.type == "nfcore" else list(spec.steps)
                state["workflow_candidates"] = []
                if spec.type == "local":
                    _fetch_local_tool_docs(state, spec)
                ui_print(f"[Planner] Auto-selected '{spec.display_name}' — {response.get('reason', '')}")
            else:
                # Ambiguous — build enriched candidates list and interrupt for user to choose
                candidates_out = []
                seen: set[str] = set()
                for c in candidates_raw:
                    name = (c.get("name") or "").strip().lower()
                    if name not in valid_names or name in seen:
                        continue
                    spec = wf_registry.get(name)
                    candidates_out.append({
                        "name": spec.name,
                        "display_name": spec.display_name,
                        "type": spec.type,
                        "description": spec.description,
                        "recommended_for": spec.recommended_for,
                        "reason": c.get("reason", ""),
                        "recommended": bool(c.get("recommended", False)),
                    })
                    seen.add(name)
                if not candidates_out:
                    candidates_out = [
                        {
                            "name": s.name,
                            "display_name": s.display_name,
                            "type": s.type,
                            "description": s.description,
                            "recommended_for": s.recommended_for,
                            "reason": "",
                            "recommended": False,
                        }
                        for s in all_specs
                    ]
                state["workflow_candidates"] = candidates_out
                state["tool_sequence"] = []
                ui_print(f"[Planner] Ambiguous — presenting {len(candidates_out)} candidates to user.")

        except Exception as e:
            ui_print(f"[Planner Error] Workflow selection failed: {e}")
            state["tool_sequence"] = []
            state["workflow_candidates"] = []

        return state

    # ── Single-tool branch ─────────────────────────────────────────────────────
    ui_print(f"\n[Planner] Tool mode — selecting subcommand...")
    tools_args = [TOOL_ARGS.get(t) for t in identified_tools]
    prompt_str = build_tool_planner_prompt(lang).format(
        input=user_input,
        history=history_str,
        tools_args=tools_args,
    )
    try:
        response = invoke_json(planner_llm, prompt_str)
        subcmd = response.get("tool")
        state["tool_sequence"] = [subcmd] if subcmd else []
        ui_print(f"[Planner] Subcommand: {subcmd}")
    except Exception as e:
        ui_print(f"[Planner Error] {e}")
        state["tool_sequence"] = []

    return state
