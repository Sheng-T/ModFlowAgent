
import os
from agent_graph.nodes.toolchain.single_tool import (
    format_single_tool_raw_output,
    summarize_single_tool_outputs,
)
from agent_graph.state import AgentState
from agent_graph.prompts.qa_prompts import build_qa_prompt, build_search_decision_prompt, build_platform_context, _load_workflow_qa_hints
from utils.llm_utils import get_llm_instance
from utils.search_utils import SearchAugmentedQA
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print
from configs.app_config import APP_SNAKE


_SHOW_RESULTS_RE = None

def _is_show_results_query(text: str) -> bool:
    import re
    global _SHOW_RESULTS_RE
    if _SHOW_RESULTS_RE is None:
        patterns = [
            r"show\s+(me\s+)?(the\s+)?results?",
            r"view\s+(the\s+)?results?",
            r"(where|find)\s+(are\s+|is\s+)?my\s+(output|results?)",
            r"(previous|last)\s+run",
            r"pipeline\s+results?",
            r"output\s+dir(ectory)?",
            r"结果在哪",  r"查看结果",  r"显示结果",
            r"看.{0,4}结果",  r"上次.{0,6}结果",
            r"结果.{0,6}哪",  r"输出在哪",  r"找.{0,4}结果",
            r"历史.{0,4}(运行|结果)",
        ]
        _SHOW_RESULTS_RE = re.compile("|".join(patterns), re.IGNORECASE)
    return bool(_SHOW_RESULTS_RE.search(text))


def _format_runs_context(runs: list, lang: str) -> str:
    if not runs:
        return ""
    lines = []
    status_zh = {"completed": "已完成", "running": "运行中",
                 "failed": "失败", "pending": "等待中", "cancelled": "已取消"}
    if lang == "en_US":
        lines.append("## Previous pipeline runs in this session\n")
        for r in runs[:8]:
            wf      = r.get("workflow_name", "unknown")
            status  = r.get("status", "unknown")
            started = (r.get("started_at") or "")[:16].replace("T", " ")
            q       = (r.get("question") or "").strip()
            rdir    = r.get("run_dir", "")
            lines.append(f"- **{wf}** — {status}" + (f"  ({started})" if started else ""))
            if q:
                lines.append(f'  - Request: "{q[:120]}"')
            if rdir:
                lines.append(f"  - Results directory: `{rdir}`")
                lines.append(f"  - *(Also accessible from the sidebar → run directory)*")
    else:
        lines.append("## 本次会话的历史流水线运行记录\n")
        for r in runs[:8]:
            wf      = r.get("workflow_name", "未知")
            status  = status_zh.get(r.get("status", ""), r.get("status", "未知"))
            started = (r.get("started_at") or "")[:16].replace("T", " ")
            q       = (r.get("question") or "").strip()
            rdir    = r.get("run_dir", "")
            lines.append(f"- **{wf}** — {status}" + (f"  （{started}）" if started else ""))
            if q:
                lines.append(f'  - 原始请求："{q[:120]}"')
            if rdir:
                lines.append(f"  - 结果目录：`{rdir}`")
                lines.append(f"  - *（也可在侧边栏的运行目录中找到）*")
    return "\n".join(lines)


def answer_general_question_node(state: AgentState, use_search: bool = True, num_searches: int = 5) -> AgentState:
    """Q&A node with optional web-search augmentation."""
    import re

    user_input = state["input"]
    augmented_context = ""
    qa_tool = None

    # detect current UI language
    try:
        import streamlit as st
        lang = st.session_state.get("lang", "en_US")
    except Exception:
        lang = "en_US"

    try:
        # 1. Determine which workflows are relevant to this question (needed before search decision)
        selected_workflow = state.get("selected_workflow", "")
        try:
            from configs.rag_config import WORKFLOW_MANIFESTS
            _all_wf_names = list(WORKFLOW_MANIFESTS.keys())
        except ImportError:
            WORKFLOW_MANIFESTS = {}
            _all_wf_names = []

        if selected_workflow:
            _relevant_wfs = [selected_workflow]
        else:
            _ui_lower = user_input.lower()
            _relevant_wfs = []
            for wf in _all_wf_names:
                if wf.replace("_", " ") in _ui_lower or wf in _ui_lower:
                    _relevant_wfs.append(wf)
                else:
                    _kws = WORKFLOW_MANIFESTS.get(wf, {}).get("qa_keywords", [])
                    if any(kw in _ui_lower for kw in _kws):
                        _relevant_wfs.append(wf)

        # 2. Determine augmented_context via one of three mutually exclusive paths:
        #    a) "show results" → scan session run history
        #    b) workflow-specific question → local RAG from workflow/tool docs (preferred over web)
        #    c) general question → optional web search
        if _is_show_results_query(user_input):
            ui_print("[QA] 'Show results' query detected — scanning session run history")
            try:
                from utils.run_tracker import find_session_runs
                from utils.user_context import get_session_dir
                _runs = find_session_runs(get_session_dir() or "")
                if _runs:
                    augmented_context = _format_runs_context(_runs, lang)
                    ui_print(f"[QA] Found {len(_runs)} run(s) in session")
                else:
                    ui_print("[QA] No runs found in session dir")
            except Exception as _e:
                ui_print(f"[QA] Run scan failed: {_e}")

        elif _relevant_wfs:
            # Workflow-specific question: use local docs (more accurate than web search for
            # platform defaults, parameter details, and tool comparisons within a workflow).
            ui_print(f"[QA] Workflow context detected: {_relevant_wfs} — using local RAG")
            _rag_parts = []
            for _wf in _relevant_wfs:
                if os.environ.get("ABLATION_NO_RAG", "0") == "1":
                    break
                _manifest = WORKFLOW_MANIFESTS.get(_wf, {})
                _wf_type = _manifest.get("type", "")
                try:
                    from configs.rag_config import RAG_INSTANCES, TOOLS_DOC, TOOL_CACHE_DIRS, WORKFLOW_PIPELINE_DOCS, WORKFLOW_CACHE_DIRS
                    from storage.rag_retriever import EnhancedMDRAG
                    _rag_llm = get_llm_instance(is_planner=False)

                    if _wf_type == "nfcore" and _wf in WORKFLOW_PIPELINE_DOCS:
                        _cache_key = f"workflow_{_wf}"
                        if _cache_key not in RAG_INSTANCES:
                            RAG_INSTANCES[_cache_key] = EnhancedMDRAG(
                                WORKFLOW_PIPELINE_DOCS[_wf], llm=_rag_llm,
                                cache_dir=WORKFLOW_CACHE_DIRS.get(_wf)
                            )
                        _ctx = RAG_INSTANCES[_cache_key].search(user_input)
                        if _ctx:
                            _rag_parts.append(f"[{_wf} docs]\n{_ctx}")

                    elif _wf_type == "local":
                        for _tool in _manifest.get("tools", []):
                            _cache_key = f"tool_{_tool}"
                            if _cache_key not in RAG_INSTANCES and _tool in TOOLS_DOC:
                                RAG_INSTANCES[_cache_key] = EnhancedMDRAG(
                                    TOOLS_DOC[_tool], llm=_rag_llm,
                                    cache_dir=TOOL_CACHE_DIRS.get(_tool)
                                )
                            if _cache_key in RAG_INSTANCES:
                                _ctx = RAG_INSTANCES[_cache_key].search(user_input)
                                if _ctx:
                                    _rag_parts.append(f"[{_tool} docs]\n{_ctx}")

                except Exception as _e:
                    ui_print(f"[QA] RAG lookup failed for {_wf}: {_e}")

            # Also check for standalone tool questions (no workflow context)
            if not _rag_parts and os.environ.get("ABLATION_NO_RAG", "0") != "1":
                try:
                    from configs.rag_config import RAG_INSTANCES, TOOLS_DOC, TOOL_CACHE_DIRS
                    from storage.rag_retriever import EnhancedMDRAG
                    _rag_llm = get_llm_instance(is_planner=False)
                    _lower_input = user_input.lower()
                    for _tool_name, _doc_path in TOOLS_DOC.items():
                        if _tool_name.lower() in _lower_input:
                            _cache_key = f"qa_tool_{_tool_name}"
                            if _cache_key not in RAG_INSTANCES:
                                RAG_INSTANCES[_cache_key] = EnhancedMDRAG(
                                    _doc_path, llm=_rag_llm,
                                    cache_dir=TOOL_CACHE_DIRS.get(_tool_name)
                                )
                            _ctx = RAG_INSTANCES[_cache_key].search(user_input)
                            if _ctx:
                                _rag_parts.append(f"[{_tool_name} docs]\n{_ctx}")
                except Exception as _e:
                    ui_print(f"[QA] Tool RAG lookup failed: {_e}")

            # Also prepend tool-specific rules from static/tools/<tool>/<tool>_rules.md
            if _rag_parts:
                try:
                    from configs.rag_config import TOOLS_RULES
                    _lower_input = user_input.lower()
                    for _tool_name, _rules_path in TOOLS_RULES.items():
                        if _tool_name.lower() in _lower_input:
                            with open(_rules_path, "r", encoding="utf-8") as _rf:
                                _rules_text = _rf.read()
                            _rag_parts.insert(0, f"[Tool Rules: {_tool_name}]\n{_rules_text}")
                            ui_print(f"[QA] Loaded rules for {_tool_name}")
                except Exception:
                    pass

            if _rag_parts:
                augmented_context = "\n\n---\n\n".join(_rag_parts)
                ui_print(f"[QA] Local RAG retrieved {len(augmented_context)} chars")
            else:
                ui_print("[QA] Local RAG returned nothing — LLM will use its own knowledge")

            # Standalone tool rules injection (guarded by ABLATION_NO_RAG)
            if os.environ.get("ABLATION_NO_RAG", "0") != "1":
                try:
                    from configs.rag_config import TOOLS_RULES
                    _lower_input = user_input.lower()
                    for _tt_name, _rr_path in TOOLS_RULES.items():
                        if _tt_name.lower() in _lower_input:
                            with open(_rr_path, "r", encoding="utf-8") as _rf:
                                _rr_text = _rf.read()
                            ui_print(f"[QA] Loaded tool rules: {_tt_name}")
                            if _rag_parts:
                                _rag_parts.insert(0, f"[Tool Rules: {_tt_name}]\n{_rr_text}")
                            else:
                                _rag_parts = [f"[Tool Rules: {_tt_name}]\n{_rr_text}"]
                            break
                except Exception as _rules_e:
                    ui_print(f"[QA] Rules injection failed: {_rules_e}")

        elif use_search:
            # General question with no workflow context: consider web search
            try:
                decision_llm = get_llm_instance(is_planner=False)
                decision_raw = decision_llm.invoke(build_search_decision_prompt(user_input))
                decision_text = (
                    decision_raw if isinstance(decision_raw, str) else decision_raw.content
                ).strip().upper()
                needs_search = decision_text.startswith("YES")
                ui_print(f"[Search] Decision: {decision_text} → {'searching' if needs_search else 'skipping'}")
            except Exception as e:
                ui_print(f"[Search] Decision call failed ({e}), skipping search")
                needs_search = False

            if needs_search:
                ui_print(f"\n[Search] Fetching reference material...")
                qa_tool = SearchAugmentedQA()
                try:
                    augmented_context = qa_tool.augment_query(user_input, num_searches=num_searches)
                    if augmented_context:
                        ui_print(f"[Search] Retrieved {len(augmented_context)} chars of context")
                    else:
                        ui_print("[Search] No results — falling back to LLM knowledge")
                except Exception as e:
                    ui_print(f"[Search] Error ({type(e).__name__}), falling back to LLM knowledge")
                    augmented_context = ""

        # 3. Load workflow-specific QA hints (hard constraints, injected regardless of RAG path)
        _hint_parts = []
        for _wf in _relevant_wfs:
            _h = _load_workflow_qa_hints(_wf, lang)
            if _h:
                _hint_parts.append(f"[{_wf}]\n{_h}")
        workflow_hints = "\n\n".join(_hint_parts)

        router_hint = state.get("router_hint", "")
        final_prompt = build_qa_prompt(user_input, augmented_context, lang,
                                       platform_context=build_platform_context(),
                                       workflow_hints=workflow_hints,
                                       router_hint=router_hint)

        # 3. call LLM
        ui_print(f"\n[LLM Answer] Invoking LLM: {user_input[:40]}...")
        answer_llm = get_llm_instance(is_planner=False)
        llm_response = answer_llm.invoke(final_prompt)
        llm_response = llm_response.strip() if isinstance(llm_response, str) else llm_response.content.strip()
        llm_response = re.sub(r"<think>.*?</think>", "", llm_response, flags=re.DOTALL).strip()

        state["final_answer"] = llm_response

    except Exception as e:
        ui_print(f"[LLM Answer] Failed: {e}")
        state["final_answer"] = (
            "Sorry, the service is temporarily unavailable." if lang == "en_US"
            else "抱歉，服务暂时不可用，无法回答您的问题。"
        )

    finally:
        if qa_tool:
            try:
                qa_tool.cleanup()
            except Exception:
                pass

    answer = state["final_answer"]
    if not answer:
        answer = "(no content)"
    
    if len(answer) > 1000:
        ui_print(f'\n[LLM Answer]\n{answer[:1000]}\n...\n[{len(answer)} chars total]')
    else:
        ui_print(f'\n[LLM Answer]\n{answer}')
    
    return state


def select_analysis_modules_node(state: AgentState) -> AgentState:
    """
    Standalone node that asks the LLM which functional analysis modules to apply.
    Sets selected_modules, module_candidates, module_confident in state.
    Runs between executor and summarizer so the result can be overridden by the user.
    """
    import json
    import re

    from tools.analyzers.registry import FUNCTIONAL_ANALYZER_MENU
    from utils.llm_utils import get_llm_instance
    from utils.lang_utils import get_lang
    from utils.ui_logger import ui_print

    lang = get_lang()
    tool_calls = state.get("tool_calls", [])

    # Use user-forced selection if already provided
    forced = state.get("forced_modules", [])
    if forced:
        ui_print(f"[ModuleSelector] Using user-forced modules: {forced}")
        state["selected_modules"] = forced
        state["module_confident"] = True
        state["module_candidates"] = []
        return state

    if not tool_calls:
        state["selected_modules"] = []
        state["module_confident"] = True
        state["module_candidates"] = []
        return state

    llm = get_llm_instance(is_planner=False)
    tool_desc = ", ".join(c["tool_name"] for c in tool_calls)
    menu_text = "\n".join(
        f'- {item["name"]}: {item["description"]}'
        for item in FUNCTIONAL_ANALYZER_MENU
    )
    all_module_names = [item["name"] for item in FUNCTIONAL_ANALYZER_MENU]

    if lang == "en_US":
        prompt = (
            f"You are a bioinformatics analysis routing expert.\n\n"
            f"Tools executed: {tool_desc}\n\n"
            f"Available analysis modules:\n{menu_text}\n\n"
            f"Select the most appropriate modules for the executed tools.\n"
            f"Set confident=true when the tool clearly maps to specific modules.\n"
            f"Set confident=false only when multiple modules are equally plausible and the correct one is ambiguous.\n\n"
            f"Return JSON only:\n"
            f'{{\"selected\": [\"module_name\"], \"confident\": true, \"candidates\": [\"module_name\", \"other\"]}}'
        )
    else:
        prompt = (
            f"你是生信分析路由专家。\n\n"
            f"已执行的工具：{tool_desc}\n\n"
            f"可用功能分析模块：\n{menu_text}\n\n"
            f"根据执行的工具选择最合适的分析模块。\n"
            f"当工具与模块映射明确时，设置 confident=true。\n"
            f"仅当多个模块同等合理、无法确定时，设置 confident=false。\n\n"
            f"只返回 JSON：\n"
            f'{{\"selected\": [\"module_name\"], \"confident\": true, \"candidates\": [\"module_name\", \"other\"]}}'
        )

    selected_modules: list[str] = []
    module_confident = True
    module_candidates: list[str] = []

    try:
        raw = llm.invoke(prompt)
        content = raw if isinstance(raw, str) else raw.content
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if "```" in content:
            content = content.split("```")[1].lstrip("json").strip()
        parsed = json.loads(content)
        selected_modules = parsed.get("selected", [])
        module_confident = bool(parsed.get("confident", True))
        module_candidates = parsed.get("candidates", selected_modules)
        ui_print(f"[ModuleSelector] selected={selected_modules} confident={module_confident} candidates={module_candidates}")
    except Exception as e:
        ui_print(f"[ModuleSelector] LLM selection failed ({e}) — using all modules as candidates")
        module_confident = False
        module_candidates = all_module_names

    state["selected_modules"] = selected_modules
    state["module_confident"] = module_confident
    state["module_candidates"] = module_candidates
    return state


def human_module_selector_node(state: AgentState) -> AgentState:
    """
    Interrupt node — the graph pauses here when module_confident=False.
    The UI renders a module selection widget and resumes with forced_modules set.
    This node itself just applies forced_modules → selected_modules and continues.
    """
    forced = state.get("forced_modules", [])
    if forced:
        state["selected_modules"] = forced
        state["module_confident"] = True
        state["module_candidates"] = []
        ui_print(f"[ModuleSelector] User selected modules: {forced}")
    return state


def _summarize_workflow(state: AgentState) -> AgentState:
    """Workflow-specific summarizer: calls per-workflow analyzer then generates a report."""
    import json
    import os
    import re

    from tools.analyzers.workflow.registry import get_workflow_analyzer
    from tools.analyzers.workflow.nf.multiqc_parser import (
        find_multiqc_data_json, find_multiqc_pngs, parse_multiqc_json,
    )

    lang         = get_lang()
    tool_calls   = state.get("tool_calls", [])
    tool_output  = state.get("tool_output", [])
    run_dir      = state.get("run_dir", "")
    workflow_name = state.get("selected_workflow", "")
    if not workflow_name and tool_calls:
        workflow_name = tool_calls[0].get("tool_name", "workflow")

    # outdir = run_dir/results  (set by build_workflow_command)
    _NF_INTERNAL = {"work", f"{APP_SNAKE}_analysis"}
    outdir = os.path.join(run_dir, "results") if run_dir else ""
    if outdir and not os.path.isdir(outdir):
        # fallback: first child directory of run_dir that isn't a nextflow internal dir
        if run_dir and os.path.isdir(run_dir):
            for entry in sorted(os.scandir(run_dir), key=lambda e: e.name):
                if (entry.is_dir()
                        and entry.name not in _NF_INTERNAL
                        and not entry.name.startswith(".")
                        and not entry.name.startswith("work")):
                    outdir = entry.path
                    break
        else:
            outdir = ""

    analysis_dir = os.path.join(run_dir, f"{APP_SNAKE}_analysis", workflow_name) if run_dir else ""
    if analysis_dir:
        os.makedirs(analysis_dir, exist_ok=True)

    if run_dir and os.path.isdir(run_dir):
        _children = [e.name for e in os.scandir(run_dir)]
        ui_print(f"[WorkflowSummarizer] run_dir contents: {_children}")
    ui_print(f"[WorkflowSummarizer] workflow={workflow_name}  outdir={outdir}")

    # ── run workflow-specific or generic analyzer ──────────────────────────────
    plot_paths: list[str] = []
    warnings:   list[str] = []
    summary:    dict      = {}

    if outdir and os.path.isdir(outdir):
        analyzer = get_workflow_analyzer(workflow_name)
        if analyzer:
            ui_print(f"[WorkflowSummarizer] Using {workflow_name}-specific analyzer")
            try:
                result     = analyzer.analyze(outdir, analysis_dir)
                summary    = result.get("summary", {})
                plot_paths = result.get("plot_paths", [])
                warnings   = result.get("warnings", [])
            except Exception as e:
                ui_print(f"[WorkflowSummarizer] Analyzer error: {e}")
                warnings.append(f"Workflow analyzer error: {e}")
        else:
            ui_print("[WorkflowSummarizer] No specific analyzer — using generic MultiQC fallback")
            mq = find_multiqc_data_json(outdir)
            if mq:
                summary["multiqc"] = parse_multiqc_json(mq)
            else:
                warnings.append("multiqc_data.json not found")
            plot_paths = find_multiqc_pngs(outdir)
    else:
        warnings.append(f"outdir not found or empty: {outdir}")

    zip_path = ""
    ui_print(f"[WorkflowSummarizer] Raw outputs in: {run_dir}")

    # ── LLM report ────────────────────────────────────────────────────────────
    raw_out   = "\n".join(tool_output).strip()[:800]
    stats_txt = json.dumps(summary, ensure_ascii=False, indent=2)[:4000]
    warn_txt  = "\n".join(f"- {w}" for w in warnings) or "None"

    if lang == "en_US":
        prompt = f"""You are a bioinformatics expert. Generate a professional Markdown report for a completed Nextflow workflow run.

[Workflow]: {workflow_name}
[Runtime output (excerpt)]:
{raw_out}

[Analysis statistics]:
{stats_txt}

[Warnings / issues]:
{warn_txt}

Requirements:
1. One-sentence overall summary (completed / partial / failed).
2. Per-sample key metrics (mapping rate, mean methylation, CpG coverage, etc. as available).
3. Biological interpretation of the results.
4. Warnings section with actionable recommendations.
5. Markdown only. Do not echo raw JSON or internal log lines."""
    else:
        prompt = f"""你是生物信息学专家，请根据以下信息生成一份专业的 Markdown 报告。

【Workflow】：{workflow_name}
【运行输出（摘要）】：
{raw_out}

【分析统计数据】：
{stats_txt}

【警告信息】：
{warn_txt}

要求：
1. 一句话总体概况（完成/部分完成/失败）。
2. 按样本列出关键指标（比对率、平均甲基化率、CpG 覆盖率等）。
3. 结合数据给出生物学解读。
4. 列出警告并给出建议。
5. 只输出 Markdown，不输出原始 JSON 或内部日志。"""

    try:
        raw = get_llm_instance(is_planner=False).invoke(prompt)
        report = raw if isinstance(raw, str) else raw.content
        report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
    except Exception as e:
        report = (f"### ✅ Workflow Completed\n\nReport generation error: {e}"
                  if lang == "en_US" else
                  f"### ✅ Workflow 已完成\n\n报告生成失败：{e}")

    state["final_answer"]        = report
    state["analysis_images"]     = [p for p in plot_paths if os.path.isfile(p)]
    state["workflow_result_zip"] = zip_path
    return state


def _summarize_local_workflow(state: AgentState) -> AgentState:
    """
    Summary branch for local (per-tool singularity) workflows.

    Three code paths:
    1. Worker still running/pending  → return a "background job started" message immediately.
    2. Worker completed              → use data from run_status.json to generate LLM report.
    3. No run_status.json (legacy)   → run analyzer + zip synchronously (old behaviour).
    """
    import json
    import os
    import re

    from utils.run_tracker import read_status as _read_status
    from utils.user_context import get_session_dir

    lang          = get_lang()
    run_dir       = state.get("run_dir", "") or get_session_dir() or ""
    workflow_name = state.get("selected_workflow", "")
    prereq_params = state.get("local_prereq_params", {})
    has_reference = bool(prereq_params.get("reference", ""))
    mod_type      = prereq_params.get("modification_type") or "m6A"
    run_meta      = {}
    run_meta_path = os.path.join(run_dir, "run_meta.json") if run_dir else ""
    if run_meta_path and os.path.isfile(run_meta_path):
        try:
            with open(run_meta_path, encoding="utf-8") as _rmf:
                run_meta = json.load(_rmf)
        except Exception as exc:
            ui_print(f"[LocalSummarizer] Could not read run_meta.json: {exc}")

    resolved_modcaller = (
        prereq_params.get("resolved_modcaller")
        or prereq_params.get("modcaller")
        or prereq_params.get("caller")
        or run_meta.get("modcaller")
        or run_meta.get("caller")
        or "unknown"
    )
    requested_modcaller = (
        prereq_params.get("requested_modcaller")
        or run_meta.get("requested_modcaller")
        or resolved_modcaller
    )
    resolved_steps = run_meta.get("resolved_step_sequence") or []
    caller_context_en = (
        f"Requested modcaller: {requested_modcaller}\n"
        f"Resolved modcaller actually used: {resolved_modcaller}\n"
        f"Resolved step sequence: {', '.join(resolved_steps) if resolved_steps else 'unknown'}\n"
        f"Reference provided: {'yes' if has_reference else 'no'}\n"
        f"Device setting: {prereq_params.get('device') or run_meta.get('device') or 'unknown'}"
    )
    caller_context_zh = (
        f"用户请求的 modcaller：{requested_modcaller}\n"
        f"本次实际使用的 modcaller：{resolved_modcaller}\n"
        f"实际执行步骤序列：{', '.join(resolved_steps) if resolved_steps else 'unknown'}\n"
        f"是否提供参考序列：{'是' if has_reference else '否'}\n"
        f"设备设置：{prereq_params.get('device') or run_meta.get('device') or 'unknown'}"
    )

    # Skip re-summarization if already done
    existing_zip = state.get("workflow_result_zip", "")
    if existing_zip and os.path.isfile(existing_zip):
        ui_print(f"[LocalSummarizer] Already summarized, skipping (zip: {existing_zip})")
        return state

    # ── Check run_status.json ─────────────────────────────────────────────────
    ws = _read_status(run_dir) if run_dir else None

    if ws and ws.get("status") in ("pending", "running"):
        # Worker is still running — return immediately; UI fragment will poll and deliver result
        ui_print(f"[LocalSummarizer] Worker {ws['status']} — returning pending message")
        _wf = workflow_name or ws.get("workflow_name", "")
        total = ws.get("total_steps", "?")
        if lang == "en_US":
            msg = (
                f"### ⏳ Pipeline running in background\n\n"
                f"**Workflow:** {_wf}  \n"
                f"**Steps:** {total}\n\n"
                f"The pipeline is running independently and will complete even if you close the browser. "
                f"Results will appear here automatically when ready. "
                f"You can also check the run directory status in the sidebar."
            )
        else:
            msg = (
                f"### ⏳ 流水线正在后台运行\n\n"
                f"**Workflow：** {_wf}  \n"
                f"**步骤数：** {total}\n\n"
                f"流水线已独立运行，关闭浏览器不影响进度。"
                f"完成后结果将自动显示在此处。"
                f"也可在侧边栏查看运行目录状态。"
            )
        state["final_answer"]        = msg
        state["analysis_images"]     = []
        state["workflow_result_zip"] = ""
        return state

    if ws and ws.get("status") == "failed":
        ui_print(f"[LocalSummarizer] Worker reported failure")
        err = ws.get("error", "unknown error")
        state["final_answer"] = (
            f"### ❌ Pipeline failed\n\n```\n{err}\n```"
            if lang == "en_US" else
            f"### ❌ 流水线执行失败\n\n```\n{err}\n```"
        )
        state["analysis_images"]     = []
        state["workflow_result_zip"] = ""
        return state

    if ws and ws.get("status") == "completed":
        # Worker finished — build LLM report from persisted data
        ui_print(f"[LocalSummarizer] Worker completed — generating LLM report from run_status")
        zip_path        = ws.get("zip_path") or ""
        plot_paths      = ws.get("analysis_images") or []
        text_summary    = ws.get("text_summary") or ""
        warnings        = ws.get("warnings") or []
        stats_txt       = text_summary[:3000] if text_summary else "{}"
        warn_txt        = "\n".join(warnings) if warnings else "None"

        data_location   = run_dir

    else:
        # ── Legacy path: no run_status.json — run analyzer synchronously ─────
        from tools.analyzers.workflow.registry import get_workflow_analyzer

        ui_print("[LocalSummarizer] No run_status.json — running analyzer synchronously")
        analysis_dir = os.path.join(run_dir, f"{APP_SNAKE}_analysis", workflow_name) if run_dir else ""
        if analysis_dir:
            os.makedirs(analysis_dir, exist_ok=True)

        summary: dict = {}
        plot_paths: list = []
        warnings: list = []
        text_summary_content = ""

        if run_dir and os.path.isdir(run_dir):
            analyzer = get_workflow_analyzer(workflow_name)
            if analyzer:
                try:
                    result     = analyzer.analyze(run_dir, analysis_dir)
                    summary    = result.get("summary", {})
                    plot_paths = result.get("plot_paths", [])
                    warnings   = result.get("warnings", [])
                    ts_path    = result.get("text_summary_path", "")
                    if ts_path and os.path.isfile(ts_path):
                        with open(ts_path, encoding="utf-8") as _f:
                            text_summary_content = _f.read()[:4000]
                    ui_print(f"[LocalSummarizer] Analyzer done: {len(plot_paths)} plots")
                except Exception as e:
                    import traceback
                    ui_print(f"[LocalSummarizer] Analyzer error: {e}\n{traceback.format_exc()}")
                    warnings.append(f"Analyzer error: {e}")

        zip_path      = ""   # 不再打包，用户直接访问 run_dir
        data_location = run_dir
        stats_txt     = text_summary_content or json.dumps(summary, ensure_ascii=False, indent=2)[:3000]
        warn_txt      = "\n".join(warnings) if warnings else "None"

    execution_context = (
        "[Execution context]\n"
        + caller_context_en
        + "\n\n[Execution context zh]\n"
        + caller_context_zh
        + "\n"
    )
    stats_txt = (execution_context + "\n" + stats_txt).strip()

    # ── Build LLM report ─────────────────────────────────────────────────────
    if lang == "en_US":
        mode_hint = (
            "The pipeline ran WITH a reference sequence, so modkit pileup produced site-level bedMethyl output. "
            "Highlight the total covered sites, high-confidence modification sites, and the top regions by mean modification fraction."
            if has_reference else
            "The pipeline ran WITHOUT a reference sequence; only modkit extract (read-level) output is available. "
            "Report total read-level calls, how many were classified as modified, and the overall fraction."
        )
        prompt = f"""You are a bioinformatics expert summarizing a {workflow_name} modification analysis.

Modification type targeted: {mod_type}
Execution context:
{caller_context_en}
{mode_hint}

[Analysis statistics]
{stats_txt}

[Warnings]
{warn_txt}

Write a concise markdown report (3–5 paragraphs):
1. One-sentence overall result (success / partial / failed).
2. State which modcaller actually produced the result and keep the description consistent with the execution context above.
3. Key quantitative findings from the stats above.
4. Biological interpretation (what the modification pattern may indicate).
5. Any warnings or caveats.
6. Data location note: raw results are stored on the server at: `{data_location}`
Do not invent tools or steps that are not listed in the execution context.
"""
    else:
        mode_hint = (
            f"本次分析提供了参考序列，modkit pileup 生成了位点级 bedMethyl 输出。"
            f"请重点报告覆盖位点总数、高置信修饰位点数和修饰比例最高的区域。"
            if has_reference else
            f"本次分析未提供参考序列，仅有 modkit extract 读段级输出。"
            f"请报告总调用数、判定为修饰的数量及整体修饰比例。"
        )
        prompt = f"""你是一位生物信息学专家，请对以下 {workflow_name} RNA 修饰分析结果进行总结。

目标修饰类型：{mod_type}
{mode_hint}

【分析统计】
{stats_txt}

【警告信息】
{warn_txt}

请撰写一份简明 Markdown 报告（3–5 段）：
1. 一句话总体结论（成功 / 部分完成 / 失败）。
2. 关键定量结果。
3. 生物学解读（修饰模式的可能意义）。
4. 注意事项或警告。
5. 数据位置：原始结果保存在服务器路径 `{data_location}`，可直接 scp/rsync 获取。
"""

    ui_print("[LocalSummarizer] Calling LLM to generate report…")
    try:
        raw    = get_llm_instance(is_planner=False).invoke(prompt)
        report = raw if isinstance(raw, str) else raw.content
        report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
    except Exception as e:
        report = (f"### Modification Analysis Complete\n\nReport generation error: {e}"
                  if lang == "en_US" else
                  f"### RNA 修饰分析完成\n\n报告生成失败：{e}")

    state["final_answer"]        = report
    state["analysis_images"]     = [p for p in plot_paths if os.path.isfile(p)]
    state["workflow_result_zip"] = zip_path
    return state


def summarize_execution_result_node(state: AgentState) -> AgentState:
    import json
    import os
    import re

    from tools.analyzers.registry import (
        extract_output_paths,
        get_file_analyzer,
        FUNCTIONAL_ANALYZER_MENU,
        get_functional_analyzer,
    )
    from utils.user_context import get_session_dir

    lang = get_lang()

    if state.get("workflow_type") == "nfcore":
        return _summarize_workflow(state)

    if state.get("workflow_type") == "local":
        return _summarize_local_workflow(state)

    tool_calls        = state.get("tool_calls", [])
    tool_output       = state.get("tool_output", [])
    pending_commands  = state.get("pending_commands", [])
    run_dir           = state.get("run_dir", "")
    result_artifacts  = state.get("result_artifacts", [])

    if not tool_calls:
        return state

    ui_print("\n[Summarizer] Starting two-stage analysis pipeline...")
    llm = get_llm_instance(is_planner=False)


    output_paths = result_artifacts or extract_output_paths(pending_commands)
    ui_print(f"[Summarizer] Detected output files: {output_paths}")


    existing_output_paths = [p for p in output_paths if os.path.isfile(p)]
    existing_output_dirs = [p for p in output_paths if os.path.isdir(p)]
    generated_output_files: list[str] = []
    for out_dir in existing_output_dirs:
        try:
            for entry in sorted(os.scandir(out_dir), key=lambda e: e.name):
                if entry.is_file():
                    generated_output_files.append(entry.path)
        except OSError:
            continue
    existing_output_paths.extend(generated_output_files)
    existing_output_paths = list(dict.fromkeys(existing_output_paths))
    if not existing_output_paths:
        state["final_answer"] = format_single_tool_raw_output(tool_output, run_dir, lang)
        state["analysis_images"] = []
        ui_print("[Summarizer] No output files detected - displaying raw command output")
        return state

    file_stats_map: dict[str, dict] = {}   # file_path -> stats dict
    for path in existing_output_paths:
        analyzer = get_file_analyzer(path)
        if analyzer is None:
            ui_print(f"[Summarizer] No analyzer for file type, skipping: {os.path.basename(path)}")
            continue
        ui_print(f"[Summarizer] Analyzing file: {os.path.basename(path)}")
        stats = analyzer.analyze(path)
        file_stats_map[path] = stats
        ui_print(f"[Summarizer] File stats done: {stats.get('type', '?')} - {len(stats)} metrics")

    selected_modules: list[str] = state.get("selected_modules", [])
    tool_desc = ", ".join(c["tool_name"] for c in tool_calls)
    ui_print(f"[Summarizer] Using analysis modules: {selected_modules}")

    if not file_stats_map and existing_output_paths:
        state["final_answer"] = summarize_single_tool_outputs(
            tool_calls=tool_calls,
            tool_output=tool_output,
            existing_output_paths=existing_output_paths,
            run_dir=run_dir,
            llm=llm,
            lang=lang,
        )
        state["analysis_images"] = []
        ui_print("[Summarizer] Unsupported output types detected - returning single-tool summary")
        return state

    functional_results: list[dict] = []
    for module_name in selected_modules:
        analyzer = get_functional_analyzer(module_name)
        if analyzer is None:
            continue
        # 找到对应类型的文件统计
        menu_item  = next((m for m in FUNCTIONAL_ANALYZER_MENU if m["name"] == module_name), {})
        need_type  = menu_item.get("required_stat_type", "")
        stats_input = next(
            (s for s in file_stats_map.values() if s.get("type") == need_type),
            None,
        )
        if stats_input is None:
            ui_print(f"[Summarizer] Skipping {module_name}: no matching {need_type} file stats")
            continue
        ui_print(f"[Summarizer] Running functional analysis: {module_name}")
        result = analyzer.analyze(stats_input)
        functional_results.append(result)

    _error_keys = {"flagstat_error", "stats_error", "error"}
    clean_stats_map = {
        path: {k: v for k, v in stats.items() if k not in _error_keys}
        for path, stats in file_stats_map.items()
    }

    stats_json      = json.dumps(clean_stats_map,      ensure_ascii=False, indent=2)
    func_json       = json.dumps(functional_results,   ensure_ascii=False, indent=2)
    raw_output_text = "\n".join(
        line for line in tool_output if str(line).strip().lower() != "null"
    ).strip()[:1000]

    if lang == "en_US":
        report_prompt = f"""You are a bioinformatics expert. Generate a professional report based on the analysis results below.

[Tools Executed]: {tool_desc}
[Raw Tool Output (summary)]:
{raw_output_text}

[File Statistics]:
{stats_json}

[Functional Analysis Results]:
{func_json}

[Background]:
- BAM files from dorado basecaller contain unaligned raw base calls; a mapped rate of 0% is completely normal and should not be flagged as an issue.
- Basecall quality should be evaluated primarily by avg_quality and read count.

Report requirements:
1. Start with a one-sentence summary (success/failure, overall quality).
2. List key statistics per file (total_reads, avg_quality, avg_read_length, etc.).
3. Provide biological interpretation based on functional analysis results.
4. If there are genuine issues or warnings (e.g. low Q-score, insufficient reads), list them separately with recommendations.
5. Use Markdown format. Do not include internal system logs or raw error fields."""
    else:
        report_prompt = f"""你是生物信息学专家，请根据以下分析结果生成一份专业的中文报告。

【执行工具】：{tool_desc}
【工具原始输出（摘要）】：
{raw_output_text}

【文件统计指标】：
{stats_json}

【功能分析结论】：
{func_json}

【背景知识】：
- dorado basecaller 输出的 BAM 是未比对的原始碱基序列，mapped rate 为 0% 是完全正常的，不应作为问题报出。
- basecall 质量评估应以平均 Q 值（avg_quality）和 reads 数量为核心指标。

报告要求：
1. 先给出一句话总结（任务是否成功、整体质量）；
2. 按文件逐一列出关键统计数字（total_reads、avg_quality、avg_read_length 等）；
3. 结合功能分析结论给出生物学解读；
4. 如有真实问题或警告（如 Q 值过低、reads 数量不足），单独列出并给出建议；
5. 语言简洁、专业，使用 Markdown 格式。不要把内部系统日志或错误字段写入报告。"""

    try:
        raw_report = llm.invoke(report_prompt)
        report     = raw_report if isinstance(raw_report, str) else raw_report.content
        report     = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
    except Exception as e:
        ui_print(f"[Summarizer] Report generation failed: {e}")
        report = (
            f"### ✅ Execution Summary\n\nTools completed, but report generation failed: {e}"
            if lang == "en_US" else
            f"### ✅ 任务执行总结\n\n工具执行完成，但报告生成失败：{e}"
        )

    plot_paths_in_run: list[str] = []
    if run_dir and os.path.isdir(run_dir):
        try:
            from tools.analyzers.file.bam_plotter import generate_bam_plots
            _plotter_available = True
        except ImportError as e:
            ui_print(f"[Summarizer] Plot module unavailable ({e}), skipping chart generation")
            _plotter_available = False

        if _plotter_available:
            for stats in file_stats_map.values():
                if stats.get("type") == "bam" and "error" not in stats:
                    try:
                        ui_print("[Summarizer] Generating BAM plots...")
                        generated = generate_bam_plots(stats, run_dir)
                        plot_paths_in_run.extend(generated)
                        ui_print(f"[Summarizer] Generated plots: {[os.path.basename(p) for p in generated]}")
                    except Exception as e:
                        ui_print(f"[Summarizer] Plot generation failed: {e}")

    session_dir   = get_session_dir()
    archived_images: list[str] = []

    if run_dir and os.path.isdir(run_dir) and session_dir and os.path.isdir(session_dir):
        analysis_result = {
            "file_stats":         file_stats_map,
            "functional_results": functional_results,
        }
        json_path = os.path.join(run_dir, "analysis.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            ui_print(f"[Summarizer] Failed to write analysis JSON: {e}")

        for entry in os.scandir(run_dir):
            if entry.is_file() and entry.name.endswith(".png"):
                archived_images.append(os.path.join(run_dir, entry.name))

        ui_print(f"[Summarizer] Run results archived to: {os.path.basename(run_dir)}")
    elif run_dir:
        ui_print("[Summarizer] Warning: run_dir or session_dir invalid, skipping archive")

    state["final_answer"]    = report
    state["analysis_images"] = archived_images
    ui_print("[Summarizer] Report generation complete")
    return state

def handle_irrelevant_request_node(state: AgentState) -> AgentState:
    ui_print("\n[Irrelevant] Generating off-topic reply...")
    lang = get_lang()
    state["final_answer"] = (
        "Sorry, I specialise in nanopore sequencing and modification detection tasks and cannot help with that."
        if lang == "en_US" else
        "抱歉，我专注于纳米孔测序和修饰检测相关的任务，无法为您提供该信息。"
    )
    ui_print(f'\n[LLM Answer] {state["final_answer"]}')
    return state


def finish_session_node(state: AgentState) -> AgentState:
    ui_print(f"\n[End] Session complete")
    return state

