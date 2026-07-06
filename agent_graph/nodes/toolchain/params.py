import importlib
import json
import os
import re
import torch
from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import build_parameter_generator_prompt
from configs import TOOL_LIST, TOOL_ARGS, DATA_PATH, TOOLS_RULES
from configs.rag_config import WORKFLOW_PIPELINE_ARGS
from tools.workflow.local import get_step_builder
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history
from utils.user_context import get_or_create_run_dir, get_session_dir
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def _list_session_files(lang: str) -> str:
    """Return a formatted string listing all files in session_dir.
    Symlinks to files are included directly; symlinks to directories are expanded one level."""
    session_dir = get_session_dir()
    if not session_dir or not os.path.isdir(session_dir):
        return "None" if lang == "en_US" else "无"
    entries = []
    for entry in sorted(os.scandir(session_dir), key=lambda e: e.name):
        if entry.is_file(follow_symlinks=True):
            size_kb = entry.stat(follow_symlinks=True).st_size / 1024
            entries.append(f"  - {entry.name}  ({size_kb:.1f} KB)  →  {entry.path}")
        elif entry.is_dir(follow_symlinks=True) and os.path.islink(entry.path):
            for sub in sorted(os.scandir(entry.path), key=lambda e: e.name):
                if sub.is_file(follow_symlinks=True):
                    size_kb = sub.stat(follow_symlinks=True).st_size / 1024
                    entries.append(f"  - {entry.name}/{sub.name}  ({size_kb:.1f} KB)  →  {sub.path}")
    if not entries:
        return "None" if lang == "en_US" else "无"
    return "\n".join(entries)


def generate_tool_params_node(state: AgentState) -> AgentState:
    param_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    rag_suggestion = state.get("rag_suggestion", {})
    tool_sequences = state.get("tool_sequence", [])
    workflow_type = state.get("workflow_type", "")
    selected_workflow = state.get("selected_workflow", "")
    pre_files = state.get("pre_files", [])
    local_prereq_params = state.get("local_prereq_params", {})

    print(f"\n[Param Generator] Configuring parameters for {len(tool_sequences)} step(s)...")
    if not tool_sequences:
        state["tool_calls"] = []
        return state

    user_feedback = state.get("user_feedback", "")
    old_tool_calls = state.get("tool_calls", [])
    final_tool_calls = []
    last_step_output_file = ""

    # ── Local workflow: try deterministic step builder first ───────────────────
    if workflow_type == "local" and selected_workflow:
        step_builder = get_step_builder(selected_workflow)
        if step_builder:
            run_dir_hint = get_or_create_run_dir() or ""
            if run_dir_hint:
                state["run_dir"] = run_dir_hint
            tool_data_path = dict(DATA_PATH.get("workflow", {}))
            tool_data_path["dorado_models"] = DATA_PATH.get("dorado", {}).get("dorado_models", "")
            session_dir = get_session_dir()
            if session_dir:
                tool_data_path["base_data_dir"] = session_dir
            if run_dir_hint:
                tool_data_path["out_dir"] = run_dir_hint

            # Pre-compute ALL step dirs so any step can reference siblings
            all_step_dirs = {
                step: os.path.join(run_dir_hint, f"step{idx + 1:02d}_{step}")
                for idx, step in enumerate(tool_sequences)
            }

            ui_print(f"[Param Generator] Using deterministic step builder for '{selected_workflow}'")
            for i, tool_name in enumerate(tool_sequences):
                step_dir = all_step_dirs[tool_name]
                result = step_builder.build_step_command(
                    tool_name, local_prereq_params, tool_data_path,
                    step_dir, all_step_dirs,
                )
                if result is None:
                    ui_print(f"[Param Generator] Skipping step {i + 1}: {tool_name}")
                    continue
                base_tool, raw_cmd = result
                final_tool_calls.append({
                    "tool_name":     tool_name,   # keeps step name for runner.py's step_dir logic
                    "_prebuilt_cmd": raw_cmd,      # build_command_for_call returns this directly
                    "_base_tool":    base_tool,    # runner.py uses this for Singularity image lookup
                    "tool_args":     {},
                })
                ui_print(f"[Param Generator] Step {i + 1} ({tool_name}): {raw_cmd[:80]}...")

            state["tool_calls"] = final_tool_calls
            return state
    # ──────────────────────────────────────────────────────────────────────────

    for i, tool_name in enumerate(tool_sequences):

        # ── workflow 模式：强制关键参数 + 可选参数提取 ────────────────────────
        if workflow_type == "nfcore" and selected_workflow:
            run_dir = get_or_create_run_dir()
            if run_dir:
                state["run_dir"] = run_dir

            input_path = ""
            if pre_files and run_dir:
                pf = pre_files[0]
                safe_name = os.path.basename(pf["filename"])
                dest = os.path.join(run_dir, safe_name)
                if not os.path.exists(dest):
                    with open(dest, "w", encoding="utf-8") as _f:
                        _f.write(pf["content"])
                    ui_print(f"[Param Generator] Re-wrote pre-file to new run_dir: {dest}")
                input_path = dest

            kwargs: dict = {
                "pipeline": selected_workflow,
                "input":    input_path,
                "outdir":   "results",
            }

            # Optional params via per-workflow params_prompt (if available)
            try:
                params_mod = importlib.import_module(
                    f"agent_graph.prompts.workflows.{selected_workflow}.params_prompt"
                )
                if hasattr(params_mod, "build_params_prompt"):
                    args_spec = json.dumps(
                        WORKFLOW_PIPELINE_ARGS.get(selected_workflow, {}),
                        ensure_ascii=False, indent=2,
                    )
                    rag_ctx = rag_suggestion.get(selected_workflow, "")
                    lang = get_lang()
                    opt_prompt = params_mod.build_params_prompt(
                        user_input, args_spec, rag_ctx, lang
                    )
                    raw = param_llm.invoke(opt_prompt)
                    raw_text = raw if isinstance(raw, str) else raw.content
                    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    if raw_text and raw_text != "{}":
                        opt_params: dict = json.loads(raw_text)
                        accepted, rejected = [], []
                        _BOOL_FILLER = {"no", "skip", "use", "with", "enable",
                                        "disable", "has", "is", "set", "all"}
                        _ui_lower = user_input.lower()
                        for k, v in opt_params.items():
                            val = v["value"] if isinstance(v, dict) and "value" in v else v
                            evidence = (v.get("evidence") or "") if isinstance(v, dict) else ""

                            # Fast-path: user explicitly wrote --param_name in their message.
                            # Bypass evidence validation entirely — intent is unambiguous.
                            _flag_in_input = (
                                f"--{k}" in user_input or
                                f"--{k.replace('_', '-')}" in user_input
                            )
                            if _flag_in_input and val in (True, False, None) or (
                                _flag_in_input and val not in (False, None, "")
                                and str(val).lower() in _ui_lower
                            ):
                                kwargs[k] = val
                                accepted.append(f"{k}(explicit flag)")
                                continue

                            # Rule 0: evidence must be present — no evidence means the LLM
                            # is inferring the param without any user-stated justification.
                            if not evidence:
                                rejected.append(f"{k}(no evidence provided)")
                                continue
                            # Rule 1: evidence must appear verbatim in user input
                            if evidence.lower() not in _ui_lower:
                                rejected.append(f"{k}(evidence not in input)")
                                continue
                            # Rule 2: for string/numeric params, evidence must explicitly
                            # mention the value being set (prevents "Pacbio" evidence for pbmm2).
                            # Exception: params that have a safe, well-known default value do not
                            # need the value to appear in evidence — the LLM infers the default
                            # when the param category is mentioned (e.g. "haplotype-level DMR"
                            # → haplotype_dmrer="dss" is correct without user saying "dss").
                            _PARAM_DEFAULTS = {"haplotype_dmrer": "dss", "population_dmrer": "dss"}
                            _is_default_val = str(val).lower() == _PARAM_DEFAULTS.get(k, "")
                            if (evidence and val not in (True, False, None, "")
                                    and not _is_default_val
                                    and str(val).lower() not in evidence.lower()):
                                rejected.append(f"{k}(evidence doesn't mention value '{val}')")
                                continue
                            # Rule 3: for boolean flags, the evidence must contain the core
                            # function word from the parameter name — prevents cross-step
                            # inference (e.g. "without re-basecalling" used for --no_trim /
                            # --reset which are unrelated pipeline steps).
                            # Prefix matching: "snv" matches core_word "snvs", etc.
                            if val in (True, False):
                                core_words = [
                                    w for w in k.lower().split("_")
                                    if w not in _BOOL_FILLER and len(w) >= 3
                                ]
                                ev_lower = evidence.lower()
                                ev_words = re.findall(r'\w+', ev_lower)
                                if core_words and not any(
                                    w in ev_lower
                                    or (len(w) > 5 and w[:4] in ev_lower)
                                    or any(w.startswith(ew) for ew in ev_words if len(ew) >= 3)
                                    for w in core_words
                                ):
                                    rejected.append(
                                        f"{k}(boolean: evidence must mention its function "
                                        f"{core_words}, got '{evidence[:40]}')"
                                    )
                                    continue
                            kwargs[k] = val
                            accepted.append(k)
                        if accepted:
                            ui_print(f"[Param Generator] Optional workflow params accepted: {accepted}")
                        if rejected:
                            ui_print(f"[Param Generator] Optional workflow params rejected (evidence mismatch): {rejected}")

                        # Hard guard: for DMR caller flags, only block NON-DEFAULT values
                        # (i.e. modkit) that the user did not explicitly request.
                        # "dss" is the pipeline default and safe to include explicitly
                        # when the user asks for haplotype/population DMR analysis.
                        _ui = user_input.lower()
                        _DMR_DEFAULTS = {"haplotype_dmrer": "dss", "population_dmrer": "dss"}
                        for _dmr_flag, _default_tool in _DMR_DEFAULTS.items():
                            if _dmr_flag in kwargs:
                                _tool_val = str(kwargs[_dmr_flag]).lower()
                                if _tool_val != _default_tool and _tool_val not in _ui:
                                    kwargs.pop(_dmr_flag)
                                    ui_print(
                                        f"[Param Generator] Hard guard removed {_dmr_flag}='{_tool_val}' "
                                        f"— non-default tool not found in user input"
                                    )

                        # Linkage enforcement: dmr_population_scale requires dmr_a and dmr_b.
                        # If the LLM accepted dmr_population_scale but omitted dmr_a/dmr_b,
                        # extract group names from user_input with a regex fallback.
                        if kwargs.get("dmr_population_scale") and (
                            "dmr_a" not in kwargs or "dmr_b" not in kwargs
                        ):
                            # Try: "<word> has ..." or "<word> vs <word>"
                            grp_names = re.findall(
                                r'\b(\w+)\s+(?:has|have)\b',
                                user_input, re.IGNORECASE,
                            )
                            if len(grp_names) < 2:
                                m = re.search(
                                    r'\b(\w+)\s+vs\.?\s+(\w+)\b',
                                    user_input, re.IGNORECASE,
                                )
                                if m:
                                    grp_names = [m.group(1), m.group(2)]
                            # filter out common stop words
                            _stop = {"sample", "the", "and", "has", "have", "who",
                                     "population", "scale", "dmr", "analysis", "please",
                                     "run", "with", "for", "use", "i", "a", "an", "each"}
                            grp_names = [g for g in grp_names if g.lower() not in _stop]
                            if "dmr_a" not in kwargs and len(grp_names) >= 1:
                                kwargs["dmr_a"] = grp_names[0]
                                ui_print(f"[Param Generator] Linkage: dmr_a set to '{grp_names[0]}' from user input")
                            if "dmr_b" not in kwargs and len(grp_names) >= 2:
                                kwargs["dmr_b"] = grp_names[1]
                                ui_print(f"[Param Generator] Linkage: dmr_b set to '{grp_names[1]}' from user input")
                            if "dmr_a" not in kwargs or "dmr_b" not in kwargs:
                                ui_print("[Param Generator] WARNING: dmr_population_scale set but "
                                         "could not extract dmr_a/dmr_b from user input — "
                                         "please add --dmr_a and --dmr_b manually in the review step")
            except ModuleNotFoundError:
                pass  # no per-workflow params_prompt, skip silently
            except Exception as e:
                ui_print(f"[Param Generator] Optional params extraction failed: {e}")

            ui_print(f"[Param Generator] nfcore kwargs: pipeline={selected_workflow}, input={input_path}, extras={[k for k in kwargs if k not in ('pipeline','input','outdir')]}")
            final_tool_calls.append({
                "tool_name": selected_workflow,
                "tool_args": {"kwargs": kwargs},
            })
            continue
        # ──────────────────────────────────────────────────────────────────────

        tool_real_name = ""
        for t in TOOL_LIST:
            if t.lower() in tool_name.lower():
                tool_real_name = t.lower()
                break
        if not tool_real_name:
            print(f"  [Warning] Skipping unrecognized tool: {tool_name}")
            continue

        current_schema = str(TOOL_ARGS.get(tool_real_name, "{}"))
        current_rag = rag_suggestion.get(tool_real_name, "No relevant documentation found.")
        # Prepend tool-specific command generation rules if available
        _rules_path = TOOLS_RULES.get(tool_real_name)
        if _rules_path and os.environ.get("ABLATION_NO_RAG", "0") != "1":
            try:
                with open(_rules_path, "r", encoding="utf-8") as _rf:
                    _rules_text = _rf.read()
                current_rag = f"[Tool Rules]\n{_rules_text}\n\n[Documentation]\n{current_rag}"
            except Exception:
                pass

        print(f"  > Configuring step {i + 1}: {tool_name} (base: {tool_real_name})")

        last_params_snapshot = ""
        for old_call in old_tool_calls:
            if tool_name.lower() == old_call.get("tool_name", "").lower():
                last_params_snapshot = json.dumps(
                    old_call.get("tool_args", {}), indent=2, ensure_ascii=False
                )
                break

        lang = get_lang()
        # For local workflows: tell the LLM where this step's output should go
        # and what prereq params (data file, reference, mod type) are available.
        local_context = ""
        if workflow_type == "local":
            run_dir_hint = get_or_create_run_dir()
            step_dir = os.path.join(run_dir_hint, f"step{i + 1:02d}_{tool_name}")
            local_context = (
                f"\n[Workflow prereq params]\n"
                f"{json.dumps({k: v for k, v in local_prereq_params.items() if not k.startswith('_')}, ensure_ascii=False, indent=2)}\n"
                f"[Step output directory]: {step_dir}\n"
                f"Place all outputs for this step inside the above directory.\n"
            )

        final_prompt = local_context + build_parameter_generator_prompt(lang).format(
            step_num=i + 1,
            tool_name=tool_name,
            schema=current_schema,
            rag=current_rag,
            session_files=_list_session_files(lang),
            user_input=user_input,
            history=history_str,
            last_params=last_params_snapshot,
            user_feedback=user_feedback if user_feedback else "N/A",
            last_output=last_step_output_file,
        )

        try:
            torch.cuda.empty_cache()
            raw_response = param_llm.invoke(final_prompt)
            content = raw_response if isinstance(raw_response, str) else raw_response.content
            clean_json_str = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            if "```json" in clean_json_str:
                clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()

            current_call = json.loads(clean_json_str)
            print(f"\n[Param Generator] {current_call}")
            final_tool_calls.append(current_call)

            args = current_call.get("tool_args", {})
            kwargs = args.get("kwargs", {})
            last_step_output_file = (
                kwargs.get("output")
                or kwargs.get("output_file")
                or kwargs.get("output_dir")
                or kwargs.get("o")
                or ""
            )
        except Exception as e:
            print(f"  [Error] Failed to configure {tool_name}: {e}")
            continue

    state["tool_calls"] = final_tool_calls
    return state
