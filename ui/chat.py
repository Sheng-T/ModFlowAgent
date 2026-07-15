
import os
import threading
import time as _time
from datetime import datetime

import streamlit as st
from configs.app_config import APP_SNAKE
from utils.i18n import _
from utils.lang_utils import get_lang
from utils.user_context import get_run_dir, set_session_context

try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    def flush_logs(): return []
    def clear_logs(): pass


# UI section 1


def _fmt_elapsed(secs: float) -> str:
    s = int(secs)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _parse_progress_log(log: str) -> None:
    if log.startswith("[PROGRESS_INIT]"):
        rest = log[len("[PROGRESS_INIT]"):].strip()
        pdict = {}
        for part in rest.split():
            if "=" in part:
                k, v = part.split("=", 1)
                pdict[k] = v
        total = int(pdict.get("total", 0))
        steps = pdict.get("steps", "").split(",") if pdict.get("steps") else []
        st.session_state["_step_progress"] = {
            "total": total,
            "steps": steps,
            "status": {s: "pending" for s in steps},
            "start_times": {},
            "elapsed": {},
        }
    elif log.startswith("[STEP_START]"):
        parts = log[len("[STEP_START]"):].strip().split(None, 1)
        if len(parts) >= 2:
            prog = st.session_state.get("_step_progress")
            if prog is not None:
                prog["status"][parts[1]] = "running"
                prog["start_times"][parts[1]] = _time.time()
    elif log.startswith("[STEP_DONE]"):
        parts = log[len("[STEP_DONE]"):].strip().split(None, 1)
        if len(parts) >= 2:
            prog = st.session_state.get("_step_progress")
            if prog is not None:
                start = prog["start_times"].get(parts[1])
                if start:
                    prog["elapsed"][parts[1]] = _time.time() - start
                prog["status"][parts[1]] = "done"
    elif log.startswith("[STEP_SKIP]"):
        parts = log[len("[STEP_SKIP]"):].strip().split(None, 1)
        if len(parts) >= 2:
            prog = st.session_state.get("_step_progress")
            if prog is not None:
                start = prog["start_times"].get(parts[1])
                if start:
                    prog["elapsed"][parts[1]] = _time.time() - start
                prog["status"][parts[1]] = "skip"
    elif log.startswith("[STEP_FAIL]"):
        parts = log[len("[STEP_FAIL]"):].strip().split(None, 1)
        if len(parts) >= 2:
            prog = st.session_state.get("_step_progress")
            if prog is not None:
                start = prog["start_times"].get(parts[1])
                if start:
                    prog["elapsed"][parts[1]] = _time.time() - start
                prog["status"][parts[1]] = "failed"
    elif log.startswith("[WORKER_STARTED]"):
        # Runner successfully spawned a detached worker; start background polling.
        rest = log[len("[WORKER_STARTED]"):].strip()
        for part in rest.split():
            if part.startswith("run_dir="):
                st.session_state["_watching_worker_run_dir"] = part[len("run_dir="):]
                break


def _render_step_progress() -> bool:
    prog = st.session_state.get("_step_progress")
    if not prog or not prog.get("steps"):
        return False

    total       = prog["total"]
    steps       = prog["steps"]
    status_map  = prog["status"]
    elapsed_map = prog["elapsed"]
    start_times = prog["start_times"]
    now         = _time.time()

    done_count = sum(1 for s in status_map.values() if s in ("done", "skip", "failed"))
    fraction   = done_count / total if total > 0 else 0
    label      = _("Step {done}/{total}").format(done=done_count, total=total)
    st.progress(fraction, text=label)

    for step_name in steps:
        status  = status_map.get(step_name, "pending")
        elapsed = elapsed_map.get(step_name)
        if status == "running":
            elapsed = now - start_times.get(step_name, now)
            icon, note = "...", f"  `{_fmt_elapsed(elapsed)}`"
        elif status == "done":
            icon = "OK"
            note = f"  `{_fmt_elapsed(elapsed)}`" if elapsed is not None else ""
        elif status == "skip":
            icon = "SKIP"
            note = "  *(resumed)*"
        elif status == "failed":
            icon = "FAIL"
            note = f"  `{_fmt_elapsed(elapsed)}`" if elapsed is not None else ""
        else:
            icon, note = "...", ""
        st.markdown(f"{icon} &nbsp; `{step_name}`{note}")

    return True


def _remove_run_dir(run_dir: str | None) -> None:
    if not run_dir or not os.path.isdir(run_dir):
        return
    try:
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)
    except Exception:
        pass


# UI section 2

_LOG_INTERNAL_PREFIXES = (
    "[ToolExecutor]",
    "[Executor] Running",
    "[Wrapper]",
    "[CmdBuilder]",
    "[Param Generator]",
    "[Review]",
    "[PrereqGenerator]",
    "[RAG",
    "[Chat]",
)

COMPLETED_PIPELINE_REPORT_PROMPT = (
    "You are a bioinformatics expert. Summarize the completed {workflow} "
    "pipeline run in a concise Markdown report (3-5 paragraphs).\n\n"
    "[Analysis statistics]\n{stats}\n\n"
    "[Warnings]\n{warnings}\n\n"
    "Include: overall result, key metrics, biological interpretation, "
    "any warnings. End with: raw results are stored on the server at "
    "`{data_location}`."
)

_DISPLAY_ICONS = {
    "Chat Q&A": "💬",
    "Tool Call": "🧰",
    "Pipeline": "🧬",
    "Auto Detect": "🤖",
    "Agent running...": "🔄",
    "Awaiting confirmation": "⏸️",
    "Awaiting workflow selection": "⏸️",
    "Awaiting workflow parameters": "⏸️",
    "Awaiting samplesheet confirmation": "⏸️",
    "Awaiting module selection": "⏸️",
    "Completed": "✅",
    "Resuming analysis...": "🔄",
    "Analysis Charts": "📊",
    "Copy": "📋",
    "Download Results (.zip)": "📥",
    "Download Report (.md)": "📥",
    "Download Report (.pdf)": "📥",
    "Confirm & Run": "✅",
    "Confirm & Continue": "✅",
    "Cancel": "❌",
    "Submit Revision": "💬",
    "Supported Tools & Pipelines": "🧰",
    "File Management": "📁",
    "New Session": "➕",
    "Link server path": "🔗",
    "Clean run products": "🗑",
    "Clean all run products": "🗑",
}
_DISPLAY_ICONS["Recommended"] = "⭐"


def _icon_text(key: str) -> str:
    icon = _DISPLAY_ICONS.get(key, "")
    text = _(key)
    return f"{icon} {text}" if icon else text

def render_log(log: str):
    stripped = log.strip()
    if not stripped:
        return
    for prefix in _LOG_INTERNAL_PREFIXES:
        if stripped.startswith(prefix):
            return

    lower = stripped.lower()
    if "\u6210\u529f" in stripped or "succeeded" in lower or "success" in lower:
        st.success(stripped)
    elif "\u5931\u8d25" in stripped or "\u9519\u8bef" in stripped or "failed" in lower or "error" in lower:
        st.error(stripped)
    elif "\u8b66\u544a" in stripped or "warning" in lower:
        st.warning(stripped)
    else:
        st.text(stripped)


def stream_events(event_iter, thinking_process: list) -> str:

    full_response = ""

    def _flush():
        flush_logs()  

    for event in event_iter:
        _flush()
        node_name = list(event.keys())[0]
        thinking_process.append(f"**{node_name}**")
        st.markdown(f"`{node_name}`")
        _flush()
        if isinstance(event.get(node_name), dict):
            for key, val in event[node_name].items():
                if key not in {"final_answer", "answer", "response", "output", "result"}:
                    if isinstance(val, (str, int, float)) and len(str(val)) < 200:
                        thinking_process.append(f"  - {key}: {val}")
        for _, node_data in event.items():
            if isinstance(node_data, dict):
                for field in ("final_answer", "answer", "response", "output", "result"):
                    if node_data.get(field):
                        full_response = node_data[field]
        _flush()
    return full_response


def _render_image_carousel(imgs: list[str], key_suffix: str = "") -> None:
    if not imgs:
        return

    lang = get_lang()
    _sfx = key_suffix or str(abs(hash(imgs[0])) % 100000)

    if len(imgs) <= 2:
        cols = st.columns(len(imgs))
        for i, p in enumerate(imgs):
            with cols[i]:
                st.image(p, caption=os.path.basename(p), width=600)
                with open(p, "rb") as f:
                    st.download_button(
                        label=_("Download {filename}").format(filename=os.path.basename(p)),
                        data=f, file_name=os.path.basename(p),
                        mime="image/png",
                        key=f"dl_img_{_sfx}_{i}",
                        width="stretch",
                    )
        return

    key = f"_img_idx_{_sfx}"
    if key not in st.session_state:
        st.session_state[key] = 0
    idx = int(st.session_state.get(key, 0))
    idx = max(0, min(idx, len(imgs) - 1))

    # UI section
    name = os.path.basename(imgs[idx])
    col_p, col_info, col_n = st.columns([1, 5, 1])
    with col_p:
        if st.button("Previous", key=f"prev_{key}", disabled=(idx == 0), width="stretch"):
            st.session_state[key] = idx - 1
            idx = idx - 1
    with col_info:
        st.markdown(
            f"<div style='text-align:center;line-height:1.4;padding-top:4px'>"
            f"<code style='font-size:0.78em;color:#888'>{name}</code>&nbsp;"
            f"<span style='font-size:0.82em;color:#aaa'>{idx + 1} / {len(imgs)}</span></div>",
            unsafe_allow_html=True,
        )
    with col_n:
        if st.button("Next", key=f"next_{key}", disabled=(idx == len(imgs) - 1), width="stretch"):
            st.session_state[key] = idx + 1
            idx = idx + 1

    # Re-read after possible update
    idx = max(0, min(st.session_state.get(key, 0), len(imgs) - 1))
    st.image(imgs[idx], width=680)
    with open(imgs[idx], "rb") as f:
        dl_label = _("Download {filename}").format(filename=os.path.basename(imgs[idx]))
        st.download_button(
            label=dl_label, data=f,
            file_name=os.path.basename(imgs[idx]),
            mime="image/png",
            key=f"dl_carousel_{key}_{idx}",
            width="stretch",
        )

    with st.expander(_("All charts"), expanded=False):
        thumb_cols = st.columns(min(len(imgs), 4))
        for ti, p in enumerate(imgs):
            with thumb_cols[ti % 4]:
                st.image(p, caption=f"{ti + 1}. {os.path.basename(p)}", width="stretch")
                if st.button(_("View {index}").format(index=ti + 1),
                             key=f"thumb_{key}_{ti}", width="stretch"):
                    st.session_state[key] = ti


def render_final(full_response: str, thinking_process: list,
                 analysis_images: list | None = None,
                 workflow_result_zip: str = "",
                 show_pdf: bool = True):
    if thinking_process:
        with st.expander(_("View thinking process"), expanded=False):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else _("Task completed"))

    if analysis_images:
        show_imgs = [p for p in analysis_images if os.path.isfile(p)]
        if show_imgs:
            st.markdown("---")
            lang = get_lang()
            title = f"**{_icon_text('Analysis Charts')}**"
            st.markdown(title)
            _render_image_carousel(show_imgs, key_suffix=f"final_{id(analysis_images)}")

    # UI section
    if full_response or analysis_images or workflow_result_zip:
        lang = get_lang()
        report_text = full_response or ""
        _key_suffix = str(len(report_text))

        st.markdown("---")
        copy_label = _icon_text("Copy")
        _render_copy_button(report_text, copy_label, key=f"copy_top_{_key_suffix}")

        if show_pdf:
            if workflow_result_zip and os.path.isfile(workflow_result_zip):
                zip_label = _icon_text("Download Results (.zip)")
                _render_zip_download(workflow_result_zip, zip_label)

            col_md, col_pdf = st.columns(2)

            with col_md:
                md_label = _icon_text("Download Report (.md)")
                md_fname = f"{APP_SNAKE}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                st.download_button(
                    label=md_label,
                    data=report_text.encode("utf-8"),
                    file_name=md_fname,
                    mime="text/markdown",
                    key=f"md_{_key_suffix}",
                    width="stretch",
                )

            with col_pdf:
                try:
                    from utils.pdf_exporter import generate_report_pdf
                    pdf_bytes = generate_report_pdf(report_text, analysis_images or [], lang)
                    pdf_label = _icon_text("Download Report (.pdf)")
                    pdf_fname = f"{APP_SNAKE}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label=pdf_label,
                        data=pdf_bytes,
                        file_name=pdf_fname,
                        mime="application/pdf",
                        key=f"pdf_{_key_suffix}",
                        width="stretch",
                    )
                except ImportError:
                    st.caption(
                        _("PDF unavailable - run `pip install fpdf2`")
                    )
                except Exception as e:
                    st.caption(f"PDF error: {e}")


def render_prereq_reviewer(app):
    """Render editable samplesheet UI when graph is paused before human_prereq_reviewer."""
    if not st.session_state.get("waiting_prereq_review"):
        return

    # Load pre_files and samplesheet_issues from graph state only once
    if "prereq_cached_files" not in st.session_state:
        config = {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        current_state = app.get_state(config)
        st.session_state.prereq_cached_files    = current_state.values.get("pre_files", [])
        st.session_state.prereq_cached_issues   = current_state.values.get("samplesheet_issues", [])
        st.session_state.prereq_cached_workflow = current_state.values.get("selected_workflow", "")
        st.session_state.prereq_cached_input    = current_state.values.get("input", "")

    pre_files     = st.session_state.prereq_cached_files
    issues        = st.session_state.get("prereq_cached_issues", [])
    wf_for_valid  = st.session_state.get("prereq_cached_workflow", "")
    user_input_v  = st.session_state.get("prereq_cached_input", "")
    with st.chat_message("assistant"):
        st.markdown(f"### {_('Review Sample Sheet')}")
        st.markdown(
            _("The system has auto-generated the samplesheet below. Please verify that file paths (BAM, reference, etc.) are correct before continuing. You can edit the content directly if needed.")
        )

        if issues:
            for issue in issues:
                msg = issue.get("message", str(issue)) if isinstance(issue, dict) else str(issue)
                if isinstance(issue, dict) and issue.get("level") == "error":
                    st.error(msg)
                else:
                    st.warning(msg)

        submitted = st.session_state.get("prereq_review_submitted", False)
        has_errors = any(
            isinstance(i, dict) and i.get("level") == "error"
            for i in issues
        )
        edited_files = []
        for pf in pre_files:
            st.markdown(f"**`{pf['filename']}`**")
            edited_content = st.text_area(
                label=pf["filename"],
                value=pf["content"],
                height=200,
                key=f"prereq_edit_{pf['filename']}",
                label_visibility="collapsed",
                disabled=submitted,
            )
            edited_files.append({"filename": pf["filename"], "content": edited_content})

        if has_errors and not submitted:
            st.info(_("Fix the errors above, then click Confirm to re-validate and continue."))

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                _icon_text("Confirm & Continue"),
                width="stretch", disabled=submitted,
            ):
                # Re-validate current edited content before proceeding
                import importlib
                new_issues: list = []
                try:
                    _validator = importlib.import_module(f"tools.workflow.nf.{wf_for_valid}.validator")
                    if hasattr(_validator, "validate_samplesheet"):
                        if os.environ.get("ABLATION_NO_VALIDATION", "0") != "1":
                            for pf in edited_files:
                                new_issues.extend(
                                    _validator.validate_samplesheet(pf["content"], user_input_v)
                                )
                except (ModuleNotFoundError, Exception):
                    pass

                if any(isinstance(i, dict) and i.get("level") == "error" for i in new_issues):
                    # Still has errors after edit; refresh displayed issues.
                    st.session_state.prereq_cached_issues = new_issues
                    st.rerun()
                else:
                    st.session_state.prereq_edited_files = edited_files
                    st.session_state.prereq_review_submitted = True
                    st.session_state.waiting_prereq_review = False
                    st.session_state.pop("prereq_cached_files", None)
                    st.session_state.pop("prereq_cached_issues", None)
                    st.rerun()
        with col2:
            if st.button(
                _icon_text("Cancel"),
                width="stretch", disabled=submitted,
            ):
                st.session_state.prereq_review_submitted = True
                st.session_state.prereq_review_cancelled = True
                st.session_state.waiting_prereq_review = False
                st.session_state.pop("prereq_cached_files", None)
                st.session_state.pop("prereq_cached_issues", None)
                st.rerun()


def render_workflow_selector(app):
    """Render workflow candidate selection UI when graph is paused before human_workflow_selector."""
    if not st.session_state.get("waiting_workflow_select"):
        return

    if "workflow_candidates_cached" not in st.session_state:
        config = {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        current_state = app.get_state(config)
        st.session_state.workflow_candidates_cached = current_state.values.get("workflow_candidates", [])
        st.session_state.workflow_selector_user_input = current_state.values.get("input", "")

    candidates = st.session_state.workflow_candidates_cached
    with st.chat_message("assistant"):
        st.markdown(f"### {_('Select a Workflow')}")
        st.markdown(_("Multiple workflows match your request. Please select one to proceed:"))

        _selector_input = st.session_state.get("workflow_selector_user_input", "")
        if _selector_input:
            from agent_graph.nodes.router.entry import _detect_data_type_mismatch
            _hint = _detect_data_type_mismatch(_selector_input.lower())
            if _hint:
                st.warning(_hint)

        submitted = st.session_state.get("workflow_select_submitted", False)

        if submitted:
            st.info(_("Processing..."))

        for cand in candidates:
            is_recommended = cand.get("recommended", False)
            label = cand.get("display_name") or cand.get("name", "")
            wf_type = cand.get("type", "")
            type_badge = "nfcore" if wf_type == "nfcore" else "local"
            reason = cand.get("reason", "")
            rec_label = (" - " + _icon_text("Recommended")) if is_recommended else ""

            with st.expander(f"{label}  {type_badge}{rec_label}", expanded=is_recommended):
                st.markdown(cand.get("description", ""))
                if reason:
                    st.caption(reason)
                btn_label = _("Select this")
                if st.button(btn_label, key=f"wf_select_{cand['name']}", width="stretch",
                             disabled=submitted):
                    st.session_state.selected_workflow_name = cand["name"]
                    st.session_state.workflow_select_submitted = True
                    st.session_state.waiting_workflow_select = False
                    st.session_state.pop("workflow_candidates_cached", None)
                    st.rerun()


def run_workflow_select_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user picks a workflow from the candidate list."""
    if not (st.session_state.get("workflow_select_submitted") and
            st.session_state.get("thread_id")):
        return

    st.session_state.workflow_select_submitted = False
    selected_name = st.session_state.pop("selected_workflow_name", None)
    if not selected_name:
        return

    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    app.update_state(config, {"selected_workflow": selected_name, "workflow_candidates": [], "user_confirmed_workflow": True},
                     as_node="human_workflow_selector")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))


        with st.status(_icon_text("Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "human_workflow_selector" in current_state.next:
            st.session_state.waiting_workflow_select     = True
            st.session_state.workflow_select_submitted   = False
            st.session_state.thinking_process            = thinking_process
            st.session_state.pop("workflow_candidates_cached", None)
            status.update(label=_icon_text("Awaiting workflow selection"), state="running")
            st.rerun()
        elif "human_local_prereq_reviewer" in current_state.next:
            st.session_state.waiting_local_prereq_review   = True
            st.session_state.local_prereq_review_submitted = False
            st.session_state.thinking_process             = thinking_process
            st.session_state.pop("local_prereq_cached_params", None)
            st.session_state.pop("local_prereq_edit_resume_dir", None)  # reset so value= default takes effect
            status.update(label=_icon_text("Awaiting workflow parameters"), state="running")
            st.rerun()
        elif "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_icon_text("Awaiting samplesheet confirmation"), state="running")
            st.rerun()
        elif "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.review_commands = current_state.values.get("review_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = current_state.values.get("run_dir", "") or get_run_dir()
            _capture_review_context(current_state)
            status.update(label=_icon_text("Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_icon_text("Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []


def render_local_prereq_reviewer(app):
    """Render editable local workflow parameters UI when graph is paused before human_local_prereq_reviewer."""
    if not st.session_state.get("waiting_local_prereq_review"):
        return

    from utils.workflow_prerequisites import get_local_prereq_params
    
    # Load local params from graph state only once; cache in session_state.
    if "local_prereq_cached_params" not in st.session_state:
        config = {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        current_state = app.get_state(config)
        selected_workflow = current_state.values.get("selected_workflow", "")
        param_defs = get_local_prereq_params(selected_workflow)
        current_params = current_state.values.get("local_prereq_params", {})
        st.session_state.local_prereq_cached_params = {
            "param_defs": param_defs,
            "current_params": current_params,
            "workflow": selected_workflow
        }

    cached = st.session_state.local_prereq_cached_params
    param_defs = cached.get("param_defs", [])
    current_params = cached.get("current_params", {})
    workflow_name = cached.get("workflow", "")
    modcaller_name = current_params.get("modcaller", "") or current_params.get("caller", "")
    modcaller_display = current_params.get("modcaller_display_name", modcaller_name)
    modcaller_candidates = current_params.get("_modcaller_candidates", [])
    requested_modcaller = current_params.get("requested_modcaller", "")
    resolved_modcaller = current_params.get("resolved_modcaller", modcaller_name)

    with st.chat_message("assistant"):
        st.markdown(f"### {_('Workflow Parameters')}: {workflow_name}")
        st.markdown(
            _("The system has auto-detected or pre-filled the workflow parameters below. Please review and edit any fields if needed before continuing.")
        )

        if (not modcaller_name) and modcaller_candidates:
            unavailable = [
                f"{item.get('display_name', item.get('name'))}: {item.get('reason', '')}"
                for item in modcaller_candidates if not item.get("available")
            ]
            if unavailable:
                st.warning(
                    _("No available modcaller matched the current configuration:") + "\n\n- " + "\n- ".join(unavailable)
                )
        for _warn_key in ("_caller_warning", "_resume_warning"):
            _warn_msg = (current_params.get(_warn_key) or "").strip()
            if _warn_msg:
                st.warning(_warn_msg)
        if current_params.get("_resume_ok"):
            st.success(_("Resume metadata matched the current request. Completed steps can be reused."))
        if requested_modcaller:
            st.caption(_("Requested modcaller: {modcaller}").format(modcaller=requested_modcaller))
        if resolved_modcaller:
            _resolved_label = current_params.get("resolved_modcaller_display_name", modcaller_display) or resolved_modcaller
            st.caption(_("Resolved modcaller: {modcaller}").format(modcaller=f"{_resolved_label} ({resolved_modcaller})"))

        submitted = st.session_state.get("local_prereq_review_submitted", False)
        edited_params = {}
         
        # Organize params in columns for better layout
        for param_def in param_defs:
            key = param_def.get("key", "")
            if key in ("resume_run_dir", "modcaller", "caller"):
                continue
            label = param_def.get("label", key)
            label = _(label)
            
            required = param_def.get("required", False)
            param_type = param_def.get("type", "text")
            default_value = param_def.get("default", "")
            current_value = current_params.get(key, default_value)
            help_text = param_def.get("hint", "") or param_def.get("description", "")
            help_text = _(help_text) if help_text else ""
            
            # Build label with required indicator: * prefix for required, optional suffix otherwise.
            if required:
                display_label = f"* {label}"
            else:
                display_label = f"{label}  (optional)" if "(optional)" not in label else label
            
            if param_type == "file":
                # For file paths, use text input
                edited_params[key] = st.text_input(
                    label=display_label,
                    value=str(current_value) if current_value else "",
                    key=f"local_prereq_edit_{key}",
                    disabled=submitted,
                    help=help_text
                )
            elif param_type == "select":
                # For select type, use selectbox
                options = param_def.get("options", [])
                edited_params[key] = st.selectbox(
                    label=display_label,
                    options=options,
                    index=options.index(current_value) if current_value in options else 0,
                    key=f"local_prereq_edit_{key}",
                    disabled=submitted,
                    help=help_text
                )
            else:
                # Default to text input
                edited_params[key] = st.text_input(
                    label=display_label,
                    value=str(current_value) if current_value else "",
                    key=f"local_prereq_edit_{key}",
                    disabled=submitted,
                    help=help_text
                )

        from tools.workflow.caller_profiles import get_modcaller_profile, get_modcaller_display_name, resolve_modcaller
        _current_mod_type = (
            st.session_state.get("local_prereq_edit_modification_type")
            or edited_params.get("modification_type")
            or current_params.get("modification_type", "")
        )
        _modcaller_options = []
        _modcaller_labels = {}
        _blocking_request = bool(current_params.get("_caller_blocking"))
        _unavailable_for_type = []
        for item in modcaller_candidates:
            name = item.get("name", "")
            if not name:
                continue
            profile = get_modcaller_profile(workflow_name, name)
            supported = profile.get("supported_modification_types", [])
            disp = item.get("display_name", name)
            if not item.get("available"):
                _unavailable_for_type.append(
                    f"{disp} ({name}) - {item.get('reason', '') or _('Unavailable')}"
                )
                continue
            profile = get_modcaller_profile(workflow_name, name)
            if _current_mod_type and _current_mod_type not in supported and _current_mod_type != "none":
                _supported_text = ", ".join(supported) if supported else _("No supported modification types")
                _unavailable_for_type.append(
                    f"{disp} ({name}) - {_('Not compatible with the selected modification type')} ({_supported_text})"
                )
                continue
            _modcaller_options.append(name)
            _modcaller_labels[name] = f"{disp} ({name})"
        _resolved_for_type = resolve_modcaller(workflow_name, _current_mod_type or current_params.get("modification_type", ""))
        if _resolved_for_type and _resolved_for_type not in _modcaller_options:
            _modcaller_options.insert(0, _resolved_for_type)
            _modcaller_labels[_resolved_for_type] = (
                f"{get_modcaller_display_name(workflow_name, _resolved_for_type)} ({_resolved_for_type})"
            )
        if _modcaller_options:
            _placeholder = "__select_compatible_modcaller__"
            _stored_modcaller = st.session_state.get("local_prereq_edit_modcaller") or current_params.get("requested_modcaller", current_params.get("modcaller", current_params.get("caller", "")))
            _needs_explicit_pick = _blocking_request and (_stored_modcaller not in _modcaller_options)
            _select_options = [_placeholder] + _modcaller_options if _needs_explicit_pick else _modcaller_options
            _current_modcaller = _stored_modcaller if _stored_modcaller in _select_options else (
                _placeholder if _needs_explicit_pick else (_resolved_for_type or _modcaller_options[0])
            )
            edited_params["modcaller"] = st.selectbox(
                label=_("Modcaller"),
                options=_select_options,
                index=_select_options.index(_current_modcaller),
                format_func=lambda x: _("Please select a compatible modcaller") if x == _placeholder else _modcaller_labels.get(x, x),
                key="local_prereq_edit_modcaller",
                disabled=submitted,
                help=_("The list is filtered by the selected modification type. If the current caller does not support that type, the workflow default will be used."),
            )
            _selected_modcaller = edited_params["modcaller"]
            if _selected_modcaller == _placeholder:
                edited_params["modcaller"] = ""
            else:
                _selected_label = _modcaller_labels.get(_selected_modcaller, _selected_modcaller)
                st.caption(
                    _("Selected modcaller: {modcaller}").format(modcaller=_selected_label)
                )
            if _unavailable_for_type:
                st.caption(_("Unavailable modcallers"))
                for _line in _unavailable_for_type:
                    st.markdown(f"- {_line}")

        # UI section
        _resume_label = _("Resume from run dir (optional, leave empty to create new)")
        _resume_help = _("Full path to an existing run_xxx dir; completed steps will be skipped automatically")
        _resume_default = st.session_state.get("resume_run_dir", "")
        resume_dir_input = st.text_input(
            label=_resume_label,
            value=_resume_default,
            key="local_prereq_edit_resume_dir",
            disabled=submitted,
            help=_resume_help,
        )
        if _resume_default and not submitted:
            st.info(
                _("Resume locked: {run_dir}").format(run_dir=f"`{_resume_default}`")
            )

        _form_errors_display = st.session_state.get("local_prereq_form_errors", [])
        if _form_errors_display:
            for _err in _form_errors_display:
                st.error(_err)
            st.info(_("Please correct the issues above and click Confirm & Continue again."))

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                _icon_text("Confirm & Continue"),
                width="stretch", disabled=submitted,
            ):
                import os as _os
                _form_errors: list[str] = []
                for _pdef in param_defs:
                    _k = _pdef.get("key", "")
                    _v = (edited_params.get(_k) or "").strip()
                    _is_path = _pdef.get("type", "") == "path" or _k in ("data_file", "reference")
                    if not _is_path:
                        continue
                    _lbl = _pdef.get("label", _k)
                    if _pdef.get("required") and not _v:
                        _form_errors.append(
                            _("{label} is required.").format(label=f"**{_lbl}**")
                        )
                    elif _v and not _os.path.exists(_v):
                        _form_errors.append(
                            _("{label}: path not found - {path}").format(label=f"**{_lbl}**", path=f"`{_v}`")
                        )
                from tools.workflow.caller_profiles import (
                    PROFILE_VERSION,
                    build_tool_sequence,
                    evaluate_modcaller_request,
                    get_modcaller_display_name,
                    get_modcaller_profile,
                    normalize_modification_type,
                )
                from agent_graph.nodes.workflows.prereq import evaluate_resume_request
                _wf = workflow_name
                _mod_type = normalize_modification_type(_wf, edited_params.get("modification_type", ""))
                _requested_modcaller = (edited_params.get("modcaller") or "").strip()
                _request_eval = evaluate_modcaller_request(_wf, _mod_type, _requested_modcaller)
                if _request_eval.get("blocking_reason"):
                    _form_errors.append(_request_eval["blocking_reason"])
                _resolved_modcaller = _request_eval.get("resolved_modcaller", "")
                _tool_sequence = build_tool_sequence(
                    _wf,
                    _resolved_modcaller,
                    _mod_type,
                    (edited_params.get("reference") or "").strip(),
                ) if _resolved_modcaller else []
                _resume_eval_params = dict(edited_params)
                _resume_eval_params["resume_run_dir"] = (resume_dir_input or st.session_state.get("resume_run_dir") or "").strip()
                _resume_eval_params["modification_type"] = _mod_type
                _resume_eval_params["_workflow"] = _wf
                _resume_eval_params["modcaller"] = _resolved_modcaller
                _resume_eval_params["caller"] = _resolved_modcaller
                _resume_eval_params["_caller_profile_version"] = PROFILE_VERSION
                _resume_ok_dir, _resume_warning = evaluate_resume_request(_resume_eval_params, _tool_sequence)
                if _resume_warning:
                    _form_errors.append(_resume_warning)
                if _form_errors:
                    st.session_state.local_prereq_form_errors = _form_errors
                    st.rerun()
                else:
                    st.session_state.pop("local_prereq_form_errors", None)
                    from utils.user_context import set_run_dir_override, clear_run_dir_override
                    _sid = st.session_state.get("current_session_id", "")
                    if _resume_ok_dir:
                        set_run_dir_override(_sid, _resume_ok_dir)
                    else:
                        clear_run_dir_override(_sid)
                    edited_params["modification_type"] = _mod_type
                    edited_params["requested_modcaller"] = _requested_modcaller
                    edited_params["resolved_modcaller"] = _resolved_modcaller
                    edited_params["modcaller"] = _resolved_modcaller
                    edited_params["caller"] = _resolved_modcaller
                    edited_params["modcaller_display_name"] = (
                        get_modcaller_display_name(_wf, _resolved_modcaller) if _resolved_modcaller else ""
                    )
                    edited_params["_caller_profile_version"] = PROFILE_VERSION
                    edited_params["_caller_runtime"] = (
                        get_modcaller_profile(_wf, _resolved_modcaller).get("runtime", {})
                        if _resolved_modcaller else {}
                    )
                    edited_params["resume_run_dir"] = _resume_ok_dir or ""
                    st.session_state.local_prereq_edited_params = edited_params
                    st.session_state.local_prereq_review_submitted = True
                    st.session_state.waiting_local_prereq_review = False
                    st.session_state.pop("local_prereq_cached_params", None)
                    st.rerun()
        with col2:
            if st.button(
                _icon_text("Cancel"),
                width="stretch", disabled=submitted,
            ):
                from utils.user_context import clear_run_dir_override
                _sid = st.session_state.get("current_session_id", "")
                clear_run_dir_override(_sid)
                st.session_state.local_prereq_review_submitted = True
                st.session_state.local_prereq_review_cancelled = True
                st.session_state.waiting_local_prereq_review = False
                st.session_state.pop("local_prereq_cached_params", None)
                st.rerun()


def render_module_selector(app):
    """Render analysis module selection UI when LLM is not confident."""
    if not st.session_state.get("waiting_module_select"):
        return

    config = {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
    current_state = app.get_state(config)
    candidates = current_state.values.get("module_candidates", [])

    with st.chat_message("assistant"):
        st.markdown(f"### {_('Select Analysis Type')}")
        st.markdown(_("The system is unsure which analysis to run. Please select the appropriate module(s):"))

        if not candidates:
            st.warning(_("No analysis modules available."))
            if st.button(_("Skip analysis"), key="skip_module_select"):
                st.session_state.waiting_module_select = False
                st.session_state.module_select_submitted = True
                st.session_state.forced_modules = []
                st.rerun()
            return

        submitted = st.session_state.get("module_select_submitted", False)
        selected = st.multiselect(
            _("Select modules"),
            options=candidates,
            default=candidates[:1] if candidates else [],
            key="module_select_choices",
            disabled=submitted,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(_("Confirm"), width="stretch", disabled=submitted):
                st.session_state.forced_modules = selected
                st.session_state.module_select_submitted = True
                st.session_state.waiting_module_select = False
                st.rerun()
        with col2:
            if st.button(_("Skip"), width="stretch", disabled=submitted):
                st.session_state.forced_modules = []
                st.session_state.module_select_submitted = True
                st.session_state.waiting_module_select = False
                st.rerun()


def get_final_from_state(current_state) -> str:
    for field in ("final_answer", "answer", "response", "output", "result"):
        val = current_state.values.get(field)
        if val:
            return val
    return ""


def _render_zip_download(zip_path: str, label: str) -> None:
    """Render a zip download via the file server (streaming). Never loads file into memory."""
    try:
        from utils.file_server import make_download_html, is_running
        import streamlit.components.v1 as components
        if is_running():
            components.html(make_download_html(zip_path, label), height=42)
            return
    except Exception:
        pass
        # File server unavailable; show server path so user can fetch it manually.
    st.warning(_("File server unavailable - fetch the file directly from the server path."))
    st.code(zip_path)


def _render_copy_button(text: str, label: str, key: str) -> None:
    """Render a clipboard copy button via JS (base64-encoded to handle all characters)."""
    import base64
    import streamlit.components.v1 as components
    b64 = base64.b64encode(text.encode("utf-8")).decode()
    copied_label = _("Copied")
    components.html(
        f"""
        <style>
        .cp-btn {{
            width:100%; padding:6px 12px; border-radius:8px;
            border:1px solid rgba(49,51,63,.2); background:#fff;
            cursor:pointer; font-size:14px; color:rgb(49,51,63);
        }}
        .cp-btn:hover {{ border-color:#ff4b4b; color:#ff4b4b; }}
        </style>
        <button class="cp-btn" onclick="
            const bytes=Uint8Array.from(atob('{b64}'),c=>c.charCodeAt(0));
            const txt=new TextDecoder('utf-8').decode(bytes);
            navigator.clipboard.writeText(txt).then(()=>{{
                this.textContent='{copied_label}';
                setTimeout(()=>this.textContent='{label}',2000);
            }});
        ">{label}</button>
        """,
        height=42,
    )


# UI section 3

def render_scroll_to_bottom_fab() -> None:
    """Inject a floating 'scroll to bottom' button when the page is not near the bottom."""
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;
          const win = window.parent;
          const BTN_ID = "agent-scroll-to-bottom-fab";
          const STYLE_ID = "agent-scroll-to-bottom-fab-style";

          function getScroller() {
            return doc.scrollingElement || doc.documentElement || doc.body;
          }

          if (!doc.getElementById(STYLE_ID)) {
            const style = doc.createElement("style");
            style.id = STYLE_ID;
            style.textContent = `
              #${BTN_ID} {
                position: fixed;
                right: 22px;
                top: 50%;
                transform: translateY(-50%);
                width: 38px;
                height: 38px;
                border: 0;
                border-radius: 999px;
                background: rgba(20, 20, 28, 0.26);
                color: #fff;
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                box-shadow: 0 8px 24px rgba(0,0,0,.18);
                display: none;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 999999;
                transition: opacity .18s ease, transform .18s ease, background .18s ease;
                opacity: .88;
              }
              #${BTN_ID}:hover {
                background: rgba(20, 20, 28, 0.42);
                transform: translateY(-50%) scale(1.04);
              }
              #${BTN_ID}:active {
                transform: translateY(-50%) scale(.97);
              }
              #${BTN_ID} .arrow {
                font-size: 18px;
                line-height: 1;
                margin-top: -1px;
              }
            `;
            doc.head.appendChild(style);
          }

          let btn = doc.getElementById(BTN_ID);
          if (!btn) {
            btn = doc.createElement("button");
            btn.id = BTN_ID;
            btn.type = "button";
            btn.setAttribute("aria-label", "Scroll to bottom");
            btn.innerHTML = '<span class="arrow">&darr;</span>';
            btn.addEventListener("click", function () {
              const scroller = getScroller();
              scroller.scrollTo({ top: scroller.scrollHeight, behavior: "smooth" });
            });
            doc.body.appendChild(btn);
          }

          function updateVisibility() {
            const scroller = getScroller();
            const viewport = win.innerHeight || doc.documentElement.clientHeight || 0;
            const distance = scroller.scrollHeight - (scroller.scrollTop + viewport);
            btn.style.display = distance > 220 ? "flex" : "none";
          }

          const scroller = getScroller();
          if (!scroller.dataset.agentScrollFabBound) {
            scroller.addEventListener("scroll", updateVisibility, { passive: true });
            win.addEventListener("resize", updateVisibility, { passive: true });
            const observer = new MutationObserver(updateVisibility);
            observer.observe(doc.body, { childList: true, subtree: true });
            scroller.dataset.agentScrollFabBound = "1";
          }

          updateVisibility();
          setTimeout(updateVisibility, 80);
          setTimeout(updateVisibility, 300);
          setTimeout(updateVisibility, 800);
        })();
        </script>
        """,
        height=0,
    )


def render_jump_to_latest_button() -> None:
    """Floating jump button fixed above the chat input and hidden near the bottom."""
    import json
    import streamlit.components.v1 as components

    label = _("Jump to latest")
    label_js = json.dumps(label)
    components.html(
        f"""
        <script>
        (function () {{
          const doc = window.parent.document;
          const win = window.parent;
          const BTN_ID = "agent-jump-latest-fab";
          const STYLE_ID = "agent-jump-latest-fab-style";
          const LABEL = {label_js};

          function getScroller() {{
            return (
              doc.querySelector('[data-testid="stAppViewContainer"]') ||
              doc.querySelector(".stAppViewContainer") ||
              doc.scrollingElement ||
              doc.documentElement ||
              doc.body
            );
          }}

          function ensureStyle() {{
            if (doc.getElementById(STYLE_ID)) return;
            const style = doc.createElement("style");
            style.id = STYLE_ID;
            style.textContent = `
              #${{BTN_ID}} {{
                position: fixed;
                right: 24px;
                bottom: 88px;
                height: 40px;
                padding: 0 14px;
                border: 0;
                border-radius: 999px;
                background: rgba(20, 20, 28, 0.78);
                color: #fff;
                display: none;
                align-items: center;
                justify-content: center;
                gap: 8px;
                cursor: pointer;
                z-index: 999999;
                box-shadow: 0 8px 24px rgba(0,0,0,.18);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                transition: opacity .18s ease, transform .18s ease, background .18s ease;
                opacity: .92;
                font-size: 13px;
                font-weight: 600;
                line-height: 1;
              }}
              #${{BTN_ID}}:hover {{
                background: rgba(20, 20, 28, 0.92);
                transform: translateY(-1px);
              }}
              #${{BTN_ID}}:active {{
                transform: translateY(0);
              }}
              #${{BTN_ID}} .arrow {{
                font-size: 16px;
                line-height: 1;
              }}
              @media (max-width: 768px) {{
                #${{BTN_ID}} {{
                  right: 16px;
                  bottom: 82px;
                  padding: 0 12px;
                  font-size: 12px;
                }}
              }}
            `;
            doc.head.appendChild(style);
          }}

          function ensureButton() {{
            let btn = doc.getElementById(BTN_ID);
            if (btn) return btn;
            btn = doc.createElement("button");
            btn.id = BTN_ID;
            btn.type = "button";
            btn.setAttribute("aria-label", LABEL);
            btn.innerHTML = '<span class="arrow">&darr;</span><span class="label"></span>';
            btn.querySelector(".label").textContent = LABEL;
            btn.addEventListener("click", function () {{
              const scroller = getScroller();
              scroller.scrollTo({{ top: scroller.scrollHeight, behavior: "smooth" }});
            }});
            doc.body.appendChild(btn);
            return btn;
          }}

          function updateVisibility() {{
            const btn = ensureButton();
            const scroller = getScroller();
            const viewport = scroller === doc.body || scroller === doc.documentElement || scroller === doc.scrollingElement
              ? (win.innerHeight || doc.documentElement.clientHeight || 0)
              : (scroller.clientHeight || win.innerHeight || 0);
            const scrollTop = scroller.scrollTop || win.scrollY || 0;
            const scrollHeight = scroller.scrollHeight || doc.body.scrollHeight || 0;
            const distance = scrollHeight - (scrollTop + viewport);
            btn.style.display = distance > 220 ? "flex" : "none";
          }}

          ensureStyle();
          ensureButton();
          const scroller = getScroller();
          if (!scroller.dataset.agentJumpLatestBound) {{
            scroller.addEventListener("scroll", updateVisibility, {{ passive: true }});
            win.addEventListener("scroll", updateVisibility, {{ passive: true }});
            win.addEventListener("resize", updateVisibility, {{ passive: true }});
            const observer = new MutationObserver(updateVisibility);
            observer.observe(doc.body, {{ childList: true, subtree: true }});
            scroller.dataset.agentJumpLatestBound = "1";
          }}

          const btn = ensureButton();
          btn.style.display = "flex";
          updateVisibility();
          setTimeout(updateVisibility, 80);
          setTimeout(updateVisibility, 300);
          setTimeout(updateVisibility, 800);
          setTimeout(updateVisibility, 1600);
        }})();
        </script>
        """,
        height=0,
    )


def render_page_bottom_anchor() -> None:
    st.markdown("""<div id="agent-page-bottom-anchor"></div>""", unsafe_allow_html=True)


def _capture_review_context(current_state) -> None:
    values = current_state.values
    local_params = values.get("local_prereq_params", {}) or {}
    st.session_state.review_is_resume = bool(local_params.get("resume_run_dir"))
    st.session_state.review_is_workflow = bool(
        values.get("selected_workflow") or values.get("workflow_type")
    )


def _load_failed_run_commands(run_dir: str) -> tuple[list[str], list[str]]:
    """Recover executable and review commands from a detached local workflow run directory."""
    import json

    job_path = os.path.join(run_dir, "job.json")
    if not run_dir or not os.path.isfile(job_path):
        return [], []
    try:
        with open(job_path, encoding="utf-8") as fh:
            job = json.load(fh)
    except Exception:
        return [], []

    commands: list[str] = []
    review_commands: list[str] = []
    for step in job.get("steps", []):
        raw_cmd = (step.get("raw_cmd") or "").strip()
        review_cmd = (step.get("review_cmd") or "").strip()
        if raw_cmd:
            commands.append(raw_cmd)
            review_commands.append(review_cmd or _simplify_review_command(raw_cmd, run_dir))
            continue
        cmd_script = step.get("cmd_script", "")
        if not cmd_script or not os.path.isfile(cmd_script):
            continue
        try:
            text = open(cmd_script, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        if text.startswith("#!/bin/bash"):
            text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.strip()
        if text:
            commands.append(text)
            review_commands.append(_simplify_review_command(text, run_dir))
    return commands, review_commands


def _simplify_review_command(raw_cmd: str, run_dir: str = "") -> str:
    import re

    cmd = (raw_cmd or "").strip()
    if not cmd:
        return cmd
    if run_dir:
        cmd = cmd.replace(run_dir, "{run_dir}")
    if "|| (" in cmd and cmd.startswith("[ -f "):
        cmd = cmd.split("|| (", 1)[1].strip()
        if cmd.endswith(")"):
            cmd = cmd[:-1].rstrip()
    cmd = re.sub(r'^\s*:\s+"[^"]+"\s*;\s*', "", cmd).strip()
    cmd = re.sub(r'\s*&&\s*touch\s+"[^"]+"\s*$', "", cmd).strip()
    return cmd


def _restore_failed_run_to_review(run_dir: str, err: str) -> None:
    """Send a failed detached worker run back to the review/regenerate UI."""
    commands, review_commands = _load_failed_run_commands(run_dir)
    if commands:
        st.session_state.pending_commands = commands
        st.session_state.review_commands = review_commands or [
            _simplify_review_command(cmd, run_dir) for cmd in commands
        ]
    st.session_state.waiting_review = True
    st.session_state.review_submitted = False
    st.session_state.current_run_dir = run_dir
    st.session_state.last_exec_error = err
    st.session_state.review_is_resume = True
    st.session_state.review_is_workflow = True


def _render_history_downloads(meta: dict, content: str):
    """Restore download buttons for historical messages from saved metadata."""
    key_base = str(hash(content))[:8]

    zip_path = meta.get("zip_path", "")
    if zip_path and os.path.isfile(zip_path):
        zip_label = _("Download Results (.zip)")
        _render_zip_download(zip_path, zip_label)

    col_md, col_pdf = st.columns(2)
    md_label  = _("Download Report (.md)")
    pdf_label = _("Download Report (.pdf)")
    with col_md:
        st.download_button(
            label=md_label,
            data=content.encode("utf-8"),
            file_name=f"{APP_SNAKE}_report.md",
            mime="text/markdown",
            key=f"hist_md_{key_base}",
            width="stretch",
        )
    with col_pdf:
        try:
            from utils.pdf_exporter import generate_report_pdf
            analysis_images = [p for p in (meta.get("analysis_images") or []) if os.path.isfile(p)]
            pdf_bytes = generate_report_pdf(content, analysis_images, get_lang())
            st.download_button(
                label=pdf_label,
                data=pdf_bytes,
                file_name=f"{APP_SNAKE}_report.pdf",
                mime="application/pdf",
                key=f"hist_pdf_{key_base}",
                width="stretch",
            )
        except Exception:
            pass


def render_history(messages: list):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and (message.get("content") or "").strip():
                copy_label = _("Copy")
                _render_copy_button(
                    message["content"],
                    copy_label,
                    key=f"hist_copy_{abs(hash(message['content']))%100000}",
                )
            thinking = message.get("thinking", "")
            if thinking and thinking.strip():
                with st.expander(_("View thinking process"), expanded=False):
                    st.markdown(thinking)
            meta = message.get("metadata") or {}
            if meta.get("zip_path") or meta.get("analysis_images"):
                hist_imgs = [p for p in (meta.get("analysis_images") or []) if os.path.isfile(p)]
                if hist_imgs:
                    st.markdown("---")
                    st.markdown(f"**{_('Analysis Charts')}**")
                    _render_image_carousel(hist_imgs, key_suffix=f"hist_{abs(hash(message['content']))%100000}")
                _render_history_downloads(meta, message["content"])


# UI section 4

def render_mode_selector():
    button_slot = st.empty()
    if not (st.session_state.waiting_for_mode and st.session_state.pending_prompt):
        return
    with button_slot.container():
        st.info(f"{_('Your input')}: {st.session_state.pending_prompt}")
        st.markdown(f"**{_('Select processing mode:')}**")
        col1, col2, col3, col4 = st.columns(4)
        clicked_mode = None
        if col1.button(_icon_text("Chat Q&A"), width="stretch"): clicked_mode = "answer"
        if col2.button(_icon_text("Tool Call"), width="stretch"): clicked_mode = "tools"
        if col3.button(_icon_text("Pipeline"), width="stretch"): clicked_mode = "workflow"
        if col4.button(_icon_text("Auto Detect"), width="stretch"): clicked_mode = "auto"
        if clicked_mode:
            button_slot.empty()
            st.session_state.ui_mode          = clicked_mode
            st.session_state.waiting_for_mode = False
        else:
            st.stop()


# UI section 5

def run_first_segment(app, store, fm, user_uid,
                      current_session_id, current_session):
    if not (st.session_state.pending_prompt and st.session_state.ui_mode
            and not st.session_state.waiting_review):
        return

    prompt  = st.session_state.pending_prompt
    ui_mode = st.session_state.ui_mode

    thread_id = current_session["thread_id"]
    st.session_state.thread_id = thread_id
    config = {"configurable": {"thread_id": thread_id}}

    st.session_state.pending_prompt   = None
    st.session_state.ui_mode          = None
    st.session_state.waiting_for_mode = False

    store.append_message(current_session_id, "user", prompt)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_process = []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))
        _apply_resume_override(current_session_id)

        with st.status(_icon_text("Agent running..."), expanded=True) as status:
            full_response = stream_events(
                app.stream({"input": prompt, "user_choice": ui_mode}, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        if "human_workflow_selector" in current_state.next:
            st.session_state.waiting_workflow_select     = True
            st.session_state.workflow_select_submitted   = False
            st.session_state.thinking_process            = thinking_process
            st.session_state.pop("workflow_candidates_cached", None)
            status.update(label=_icon_text("Awaiting workflow selection"), state="running")
        elif "human_local_prereq_reviewer" in current_state.next:
            st.session_state.waiting_local_prereq_review   = True
            st.session_state.local_prereq_review_submitted = False
            st.session_state.thinking_process             = thinking_process
            st.session_state.pop("local_prereq_cached_params", None)
            st.session_state.pop("local_prereq_edit_resume_dir", None)  # reset so value= default takes effect
            status.update(label=_icon_text("Awaiting workflow parameters"), state="running")
        elif "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_icon_text("Awaiting samplesheet confirmation"), state="running")
        elif "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = current_state.values.get("run_dir", "") or get_run_dir()
            status.update(label=_icon_text("Awaiting confirmation"), state="running")
        elif "human_module_selector" in current_state.next:
            st.session_state.waiting_module_select  = True
            st.session_state.module_select_submitted = False
            st.session_state.thinking_process       = thinking_process
            status.update(label=_icon_text("Awaiting module selection"), state="running")
        else:
            status.update(label=_icon_text("Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )

    if (st.session_state.waiting_review
            or st.session_state.get("waiting_workflow_select")
            or st.session_state.get("waiting_module_select")
            or st.session_state.get("waiting_prereq_review")
            or st.session_state.get("waiting_local_prereq_review")):
        st.rerun()


# UI section 6

def render_review(app):
    if not st.session_state.waiting_review:
        return

    with st.chat_message("assistant"):
        last_error = st.session_state.get("last_exec_error")
        if last_error:
            st.error(f"### {_('Last run failed - commands have been auto-corrected')}")
            with st.expander(_("View error details"), expanded=True):
                st.code(last_error, language="text")
            st.markdown(f"**{_('Review the commands below and confirm to continue.')}**")
        else:
            st.markdown(f"### {_('Pending commands - please confirm')}")

        pre_files = app.get_state(
            {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        ).values.get("pre_files", [])
        if pre_files:
            st.markdown(f"**{_('Pre-requisite files')}**")
            for pf in pre_files:
                with st.expander(f"`{pf['filename']}`", expanded=True):
                    st.code(pf["content"], language="csv")

        if st.session_state.pending_commands:
            st.markdown(f"**{_('Commands to execute')}**")
            review_commands = st.session_state.get("review_commands") or st.session_state.pending_commands
            for i, cmd in enumerate(review_commands, 1):
                st.markdown(f"**{_('Step')} {i}**")
                st.code(cmd, language="bash")
        else:
            st.info(_("Command list is empty - check parameter generation"))

        st.markdown("---")
        submitted  = st.session_state.review_submitted
        confirming = st.session_state.get("confirming_execute", False)

        if submitted:
            decision = st.session_state.get("resume_decision")
            if decision == "cancel":
                st.warning(_("Cancelling..."))
            elif decision == "modify":
                st.info(_("Regenerating commands..."))
            else:
                st.info(_("Submitted - task is running, please wait..."))

        st.text_input(_("Revision notes (fill in before submitting)"),
                      key="review_feedback", disabled=submitted)
        col1, col2, col3 = st.columns(3)
        with col1:
            if not confirming:
                if st.button(_icon_text("Confirm & Run"),
                             width="stretch", disabled=submitted):
                    st.session_state.confirming_execute = True
                    st.rerun()
            else:
                st.warning(_("This will run on the server immediately. Are you sure?"))
                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button(_("Yes, run it"),
                                 width="stretch", type="primary",
                                 disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.session_state.review_submitted   = True
                        st.session_state.resume_decision    = "execute"
                        st.session_state.pop("last_exec_error", None)
                        st.rerun()
                with no_col:
                    if st.button(_("Let me check again"),
                                 width="stretch", disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.rerun()
        with col2:
            if st.button(_icon_text("Cancel"),
                         width="stretch",
                         disabled=submitted or confirming):
                st.session_state.review_submitted = True
                st.session_state.resume_decision  = "cancel"
                st.session_state.pop("last_exec_error", None)
                st.rerun()
        with col3:
            if st.button(_icon_text("Submit Revision"),
                         width="stretch",
                         disabled=submitted or confirming):
                if st.session_state.review_feedback.strip():
                    st.session_state.review_submitted = True
                    st.session_state.resume_decision  = "modify"
                    st.rerun()
                else:
                    st.warning(_("Please fill in revision notes first"))



def render_review_v2(app):
    """Cleaner bilingual review UI for command confirmation / resume."""
    if not st.session_state.waiting_review:
        return

    with st.chat_message("assistant"):
        is_resume = bool(st.session_state.get("review_is_resume"))
        last_error = st.session_state.get("last_exec_error")

        if last_error:
            st.error(f"### {_('Last run failed')}")
            with st.expander(_("View error details"), expanded=True):
                st.code(last_error, language="text")
            st.markdown(f"**{_('Review the commands below and confirm to continue.')}**")
        else:
            st.markdown(f"### {_('Pending commands - please confirm')}")

        pre_files = app.get_state(
            {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        ).values.get("pre_files", [])
        if pre_files:
            st.markdown(f"**{_('Pre-requisite files')}**")
            for pf in pre_files:
                with st.expander(f"`{pf['filename']}`", expanded=True):
                    st.code(pf["content"], language="csv")

        if st.session_state.pending_commands:
            st.markdown(f"**{_('Commands for this run')}**")
            review_commands = st.session_state.get("review_commands") or st.session_state.pending_commands
            for i, cmd in enumerate(review_commands, 1):
                st.markdown(f"**{_('Step')} {i}**")
                st.code(cmd, language="bash")
        else:
            st.info(_("Command list is empty - check parameter generation"))

        st.markdown("---")
        submitted = st.session_state.review_submitted
        confirming = st.session_state.get("confirming_execute", False)

        if submitted:
            decision = st.session_state.get("resume_decision")
            if decision == "cancel":
                st.warning(_("Cancelling..."))
            elif decision == "modify":
                st.info(_("Regenerating commands..."))
            else:
                st.info(_("Submitted - task is running, please wait..."))

        st.text_input(
            _("Revision notes (fill in before submitting)"),
            key="review_feedback",
            disabled=submitted,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if not confirming:
                if st.button(
                    _icon_text("Confirm & Continue") if is_resume else _icon_text("Confirm & Run"),
                    width="stretch",
                    disabled=submitted,
                ):
                    st.session_state.confirming_execute = True
                    st.rerun()
            else:
                if is_resume:
                    st.warning(
                        _("This will continue the selected run on the server immediately. Valid completed steps will be skipped; failed or unfinished steps will run again.")
                    )
                else:
                    st.warning(_("This will run on the server immediately. Are you sure?"))
                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button(
                        _("Yes, continue") if is_resume else _("Yes, run it"),
                        width="stretch",
                        type="primary",
                        disabled=submitted,
                    ):
                        st.session_state.confirming_execute = False
                        st.session_state.review_submitted = True
                        st.session_state.resume_decision = "execute"
                        st.session_state.pop("last_exec_error", None)
                        st.rerun()
                with no_col:
                    if st.button(
                        _("Let me review again") if is_resume else _("Let me check again"),
                        width="stretch",
                        disabled=submitted,
                    ):
                        st.session_state.confirming_execute = False
                        st.rerun()
        with col2:
            if st.button(
                _icon_text("Cancel"),
                width="stretch",
                disabled=submitted or confirming,
            ):
                st.session_state.review_submitted = True
                st.session_state.resume_decision = "cancel"
                st.session_state.pop("last_exec_error", None)
                st.rerun()
        with col3:
            if st.button(
                _icon_text("Submit Revision"),
                width="stretch",
                disabled=submitted or confirming,
            ):
                if st.session_state.review_feedback.strip():
                    st.session_state.review_submitted = True
                    st.session_state.resume_decision = "modify"
                    st.rerun()
                else:
                    st.warning(_("Please fill in revision notes first"))
def run_local_prereq_review_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user confirms/edits the local workflow parameters."""
    if not (st.session_state.get("local_prereq_review_submitted") and
            st.session_state.get("thread_id")):
        return

    st.session_state.local_prereq_review_submitted = False
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.session_state.pop("local_prereq_review_cancelled", False):
        app.update_state(config, {"next_node": "end_node"}, as_node="human_local_prereq_reviewer")
        st.info(_("Task cancelled"))
        return

    edited_params = st.session_state.pop("local_prereq_edited_params", {})
    if edited_params:
        from tools.workflow.caller_profiles import (
            PROFILE_VERSION,
            build_tool_sequence,
            evaluate_modcaller_request,
            get_modcaller_display_name,
            get_modcaller_profile,
            normalize_modification_type,
        )
        from agent_graph.nodes.workflows.prereq import evaluate_resume_request
        current_state_pre = app.get_state(config)
        selected_wf = current_state_pre.values.get("selected_workflow", "")
        edited_params["modification_type"] = normalize_modification_type(
            selected_wf,
            edited_params.get("modification_type", ""),
        )
        edited_params["device"] = (edited_params.get("device") or "auto").strip() or "auto"
        edited_params["_workflow"] = selected_wf
        manual_modcaller = (edited_params.get("requested_modcaller") or edited_params.get("modcaller") or edited_params.get("caller") or "").strip()
        request_eval = evaluate_modcaller_request(
            selected_wf,
            edited_params["modification_type"],
            manual_modcaller,
        )
        modcaller_name = request_eval.get("resolved_modcaller", "")
        modcaller_profile = get_modcaller_profile(selected_wf, modcaller_name) if modcaller_name else {}
        edited_params["requested_modcaller"] = request_eval.get("requested_modcaller", "")
        edited_params["resolved_modcaller"] = modcaller_name
        edited_params["modcaller"] = modcaller_name
        edited_params["modcaller_display_name"] = (
            get_modcaller_display_name(selected_wf, modcaller_name) if modcaller_name else ""
        )
        edited_params["caller"] = modcaller_name
        edited_params["_caller_profile_version"] = PROFILE_VERSION
        edited_params["_caller_runtime"] = modcaller_profile.get("runtime", {})
        edited_params["_device_transform"] = modcaller_profile.get("device_transform", "passthrough")
        edited_params["_entrypoint"] = modcaller_profile.get("entrypoint", "")
        edited_params["_workdir"] = modcaller_profile.get("workdir", "")
        tool_sequence = build_tool_sequence(
            selected_wf,
            modcaller_name,
            edited_params["modification_type"],
            (edited_params.get("reference") or "").strip(),
        )
        resume_run_dir, _resume_warning = evaluate_resume_request(edited_params, tool_sequence)
        edited_params["resume_run_dir"] = resume_run_dir or ""
        state_update: dict = {
            "local_prereq_params": edited_params,
            "tool_sequence": tool_sequence,
        }
        if resume_run_dir:
            state_update["run_dir"] = resume_run_dir
        app.update_state(config, state_update, as_node="human_local_prereq_reviewer")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))
        _apply_resume_override(current_session_id)

        with st.status(_icon_text("Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_icon_text("Awaiting samplesheet confirmation"), state="running")
            st.rerun()
        elif "executor" in current_state.next:
            st.session_state.pending_commands  = current_state.values.get("pending_commands", [])
            st.session_state.review_commands   = current_state.values.get("review_commands", [])
            st.session_state.waiting_review    = True
            st.session_state.review_submitted  = False
            st.session_state.thinking_process  = thinking_process
            st.session_state.current_run_dir   = current_state.values.get("run_dir", "") or get_run_dir()
            _capture_review_context(current_state)
            status.update(label=_icon_text("Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_icon_text("Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []



def run_prereq_review_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user confirms/edits the samplesheet."""
    if not (st.session_state.get("prereq_review_submitted") and
            st.session_state.get("thread_id")):
        return

    st.session_state.prereq_review_submitted = False
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.session_state.pop("prereq_review_cancelled", False):
        app.update_state(config, {"next_node": "end_node"}, as_node="human_prereq_reviewer")
        st.info(_("Task cancelled"))
        return

    edited_files = st.session_state.pop("prereq_edited_files", [])
    if edited_files:
        app.update_state(config, {"pre_files": edited_files}, as_node="human_prereq_reviewer")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))


        with st.status(_icon_text("Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "executor" in current_state.next:
            st.session_state.pending_commands  = current_state.values.get("pending_commands", [])
            st.session_state.review_commands   = current_state.values.get("review_commands", [])
            st.session_state.waiting_review    = True
            st.session_state.review_submitted  = False
            st.session_state.thinking_process  = thinking_process
            st.session_state.current_run_dir   = current_state.values.get("run_dir", "") or get_run_dir()
            _capture_review_context(current_state)
            status.update(label=_icon_text("Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_icon_text("Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []



def run_module_select_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user has confirmed module selection."""
    if not (st.session_state.get("module_select_submitted") and
            st.session_state.get("thread_id") and
            not st.session_state.get("waiting_module_select")):
        return

    st.session_state.module_select_submitted = False
    forced_modules = st.session_state.pop("forced_modules", [])
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    app.update_state(config, {"forced_modules": forced_modules}, as_node="human_module_selector")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))


        with st.status(_icon_text("Resuming analysis..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)
        status.update(label=_icon_text("Completed"), state="complete")
        if not full_response:
            full_response = get_final_from_state(current_state)
        _imgs = current_state.values.get("analysis_images", [])
        _zip  = current_state.values.get("workflow_result_zip", "")
        _tc   = current_state.values.get("tool_calls", [])
        _show_pdf = bool(_tc or _imgs or _zip)
        render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("Task completed"),
            "\n".join(thinking_process),
            metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
        )
        st.session_state.thinking_process = []



class _AgentResult:
    """Container for app.stream() results shared across threads."""
    def __init__(self):
        self.events: list = []
        self.done: bool   = False
        self.error        = None


def _run_agent_in_background(app, config, result: _AgentResult,
                             user_uid: int, current_session_id: str,
                             session_dir: str, lang: str = ""):
    try:
        set_session_context(user_uid, current_session_id, session_dir, lang=lang)
        for event in app.stream(None, config=config):
            result.events.append(event)
    except BaseException as e:
        # Catch BaseException (not just Exception) so that SystemExit / KeyboardInterrupt
        # raised by subprocess cleanup or OOM-killer signals in the graph nodes are
        # recorded as errors instead of silently killing the thread or propagating.
        import traceback
        tb = traceback.format_exc()
        result.error = f"{type(e).__name__}: {e}\n\n{tb}"
    finally:
        result.done = True



def run_second_segment(app, store, fm, user_uid, current_session_id):
    _rd  = st.session_state.get("resume_decision")
    _tid = st.session_state.get("thread_id")
    if _rd and _tid:
        decision = st.session_state.resume_decision
        st.session_state.resume_decision = None
        st.session_state.waiting_review  = False
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        if decision == "cancel":
            app.update_state(config, {"next_node": "end_node"}, as_node="human_reviewer")
            _remove_run_dir(st.session_state.pop("current_run_dir", None))
            st.info(_("Task cancelled"))
            return

        if decision == "modify":
            app.update_state(
                config,
                {"next_node": "param_generator",
                 "user_feedback": st.session_state.review_feedback},
                as_node="human_reviewer",
            )
            st.session_state.pop("review_feedback", None)

        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))


        _bg_lang = st.session_state.get("lang", "")
        result = _AgentResult()
        t = threading.Thread(target=_run_agent_in_background,
                             args=(app, config, result, user_uid, current_session_id,
                                   fm.session_dir(user_uid, current_session_id), _bg_lang),
                             daemon=True)
        t.start()
        st.session_state._agent_bg_result    = result
        st.session_state._agent_bg_thread    = t
        st.session_state._agent_thinking     = st.session_state.thinking_process or []
        st.session_state._agent_user_uid     = user_uid
        st.session_state._agent_session_id   = current_session_id
        st.rerun()


def _apply_resume_override(current_session_id: str) -> None:
    """If resume_run_dir is set in session_state, lock it as the run_dir override."""
    _rdir = st.session_state.get("resume_run_dir", "")
    if _rdir and current_session_id:
        from utils.user_context import set_run_dir_override
        set_run_dir_override(current_session_id, _rdir)


def _cleanup_agent_bg_state():
    for key in ("_agent_bg_result", "_agent_bg_thread", "_agent_thinking",
                "_agent_user_uid", "_agent_session_id", "_agent_log_buf",
                "_step_progress"):
        st.session_state.pop(key, None)
    # Clear any resume lock so the next run creates a fresh dir
    from utils.user_context import clear_run_dir_override
    _sid = st.session_state.get("current_session_id", "")
    if _sid:
        clear_run_dir_override(_sid)
    st.session_state.pop("resume_run_dir", None)


def _queue_full_rerun(reason: str = "") -> None:
    st.session_state["_queued_full_rerun"] = True
    if reason:
        st.session_state["_queued_full_rerun_reason"] = reason


@st.fragment(run_every=5)
def _poll_agent_fragment(app, store, current_session_id: str):
    result: _AgentResult = st.session_state.get("_agent_bg_result")
    if result is None:
        return

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("_agent_thinking", [])
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        while result.events:
            event = result.events.pop(0)
            node_name = list(event.keys())[0]
            thinking_process.append(f"**{node_name}**")
        for log in flush_logs():
            st.session_state.setdefault("_agent_log_buf", []).append(log)
            _parse_progress_log(log)
        st.session_state._agent_thinking = thinking_process

        has_progress = _render_step_progress()

        log_buf = st.session_state.get("_agent_log_buf", [])
        if log_buf:
            with st.expander(_("Execution log"), expanded=not has_progress):
                st.code("\n".join(log_buf), language=None)

        if not result.done:
            if has_progress:
                prog = st.session_state.get("_step_progress", {})
                all_steps_finished = all(
                    s in ("done", "skip", "failed")
                    for s in prog.get("status", {}).values()
                ) if prog.get("status") else False
                if all_steps_finished:
                    st.info(_("Analyzing results and generating report, please wait..."))
            else:
                st.info(_("Running workflow, please wait..."))
            return

        for log in flush_logs():
            st.session_state.setdefault("_agent_log_buf", []).append(log)
            _parse_progress_log(log)

        if result.error:
            st.error(f"Agent error: {result.error}")
            _cleanup_agent_bg_state()
            return

        try:
            current_state = app.get_state(config)
        except Exception as e:
            st.error(f"Failed to retrieve agent state: {e}")
            _cleanup_agent_bg_state()
            return

        try:
            if "human_module_selector" in current_state.next:
                st.session_state.waiting_module_select = True
                st.session_state.module_select_submitted = False
                st.session_state.thinking_process = thinking_process
                _cleanup_agent_bg_state()
                _queue_full_rerun("agent_to_module_selector")
            elif "param_generator" in current_state.next or "executor" in current_state.next:
                history = current_state.values.get("chat_history", [])
                last_error = None
                for msg in reversed(history):
                    content = msg.get("content", "")
                    if msg.get("role") == "assistant" and ("failed" in content.lower() or "\u5931\u8d25" in content):
                        last_error = content
                        break
                st.session_state.pending_commands = current_state.values.get("pending_commands", [])
                st.session_state.review_commands = current_state.values.get("review_commands", [])
                st.session_state.waiting_review = True
                st.session_state.review_submitted = False
                st.session_state.thinking_process = thinking_process
                st.session_state.current_run_dir = current_state.values.get("run_dir", "") or get_run_dir()
                st.session_state.last_exec_error = last_error
                _capture_review_context(current_state)
                _cleanup_agent_bg_state()
                _queue_full_rerun("agent_to_review")
            else:
                full_response = get_final_from_state(current_state)
                _imgs = current_state.values.get("analysis_images", [])
                _zip = current_state.values.get("workflow_result_zip", "")
                store.append_message(
                    current_session_id,
                    "assistant",
                    full_response if full_response else _("Task completed"),
                    "\n".join(thinking_process),
                    metadata={"zip_path": _zip, "analysis_images": _imgs} if _zip or _imgs else None,
                )
                st.session_state.thinking_process = []
                _wrd = current_state.values.get("run_dir", "")
                if _wrd and current_state.values.get("workflow_type") == "local":
                    try:
                        from utils.run_tracker import read_status as _rs
                        _ws = _rs(_wrd)
                        if _ws and _ws.get("status") in ("pending", "running"):
                            st.session_state["_watching_worker_run_dir"] = _wrd
                    except Exception:
                        pass
                _cleanup_agent_bg_state()
                _queue_full_rerun("agent_completed")
        except Exception as e:
            import traceback
            st.error(f"Error processing completed task: {e}\n\n{traceback.format_exc()}")
            _cleanup_agent_bg_state()


def render_agent_poller(app, store, current_session_id: str):
    _poll_agent_fragment(app, store, current_session_id)
    if st.session_state.pop("_queued_full_rerun", False):
        st.session_state.pop("_queued_full_rerun_reason", None)
        st.rerun()


@st.fragment(run_every=10)
def _poll_worker_fragment(store, current_session_id: str, watch_dir: str):
    if not watch_dir:
        return
    from utils.run_tracker import read_status as _rs
    ws = _rs(watch_dir)
    if ws is None:
        return

    with st.chat_message("assistant"):
        _poll_worker_fragment_body(store, current_session_id, watch_dir, ws)


def _poll_worker_fragment_body(store, current_session_id: str, watch_dir: str, ws: dict):
    status = ws.get("status", "pending")
    if status in ("pending", "running"):
        total = ws.get("total_steps", "?")
        current = ws.get("current_step") or "-"
        idx = ws.get("current_step_index", 0)
        _col_info, _col_cancel = st.columns([5, 1])
        with _col_info:
            st.info(_("Pipeline running - step {index}/{total}: {step} (refreshes every 10 s)").format(
                index=idx + 1,
                total=total,
                step=f"`{current}`",
            ))
        with _col_cancel:
            if st.button(_("Cancel"), key="cancel_worker_btn", width="stretch"):
                _pid = ws.get("pid")
                if _pid:
                    import signal as _sig
                    _killed = False
                    try:
                        import subprocess as _sp
                        _sp.run(["pkill", "-TERM", "-s", str(_pid)], capture_output=True)
                        _killed = True
                    except Exception:
                        pass
                    if not _killed:
                        try:
                            os.killpg(os.getpgid(_pid), _sig.SIGTERM)
                        except (ProcessLookupError, OSError):
                            try:
                                os.kill(_pid, _sig.SIGTERM)
                            except (ProcessLookupError, OSError):
                                pass
                from utils.run_tracker import write_status as _ws
                _ws(watch_dir, {**ws,
                    "status": "cancelled",
                    "finished_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "error": "Cancelled by user.",
                })
                st.session_state.pop("_watching_worker_run_dir", None)
                _queue_full_rerun("worker_cancelled")
        _wlog = os.path.join(watch_dir, "worker.log")
        try:
            if os.path.isfile(_wlog):
                _log_txt = open(_wlog, encoding="utf-8", errors="replace").read().strip()
                if _log_txt:
                    with st.expander(_("Worker log"), expanded=False):
                        st.code(_log_txt[-4000:], language=None)
        except Exception:
            pass
        _slog = os.path.join(watch_dir, "worker_stderr.log")
        try:
            if os.path.isfile(_slog):
                _err_txt = open(_slog, encoding="utf-8", errors="replace").read().strip()
                if _err_txt:
                    with st.expander(_("Worker error log"), expanded=True):
                        st.code(_err_txt[-3000:], language="python")
        except Exception:
            pass
        return

    st.session_state.pop("_watching_worker_run_dir", None)

    if status == "cancelled":
        msg = f"### {_('Pipeline cancelled by user.')}"
        store.append_message(current_session_id, "assistant", msg, "")
        _queue_full_rerun("worker_cancelled_done")
        return

    if status == "failed":
        err = ws.get("error", "unknown error")
        msg = f"### {_('Pipeline failed')}\n\n```\n{err}\n```"
        store.append_message(current_session_id, "assistant", msg, "")
        _restore_failed_run_to_review(watch_dir, err)
        _queue_full_rerun("worker_failed")
        return

    if status == "completed":
        plot_paths = ws.get("analysis_images") or []
        text_summary = ws.get("text_summary") or ""
        warnings = ws.get("warnings") or []
        wf_name = ws.get("workflow_name", "workflow")
        data_location = ws.get("run_dir") or watch_dir
        stats_txt = text_summary[:3000] if text_summary else "{}"
        warn_txt = "\n".join(warnings) if warnings else "None"

        import re
        from utils.llm_utils import get_llm_instance

        prompt = _(COMPLETED_PIPELINE_REPORT_PROMPT).format(
            workflow=wf_name,
            stats=stats_txt,
            warnings=warn_txt,
            data_location=data_location,
        )

        with st.spinner(_("Generating report...")):
            try:
                raw = get_llm_instance(is_planner=False).invoke(prompt)
                report = raw if isinstance(raw, str) else raw.content
                report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
            except Exception as exc:
                report = (
                    f"### {_('Pipeline Complete')}\n\n{_('Report generation error: {error}').format(error=exc)}"
                )

        valid_imgs = [p for p in plot_paths if os.path.isfile(p)]
        meta = {"analysis_images": valid_imgs, "worker_run_dir": data_location}
        store.append_message(current_session_id, "assistant", report, "", metadata=meta)
        _queue_full_rerun("worker_completed")


def render_worker_poller(store, current_session_id: str):
    watch_dir = st.session_state.get("_watching_worker_run_dir", "")
    _poll_worker_fragment(store, current_session_id, watch_dir)
    if st.session_state.pop("_queued_full_rerun", False):
        st.session_state.pop("_queued_full_rerun_reason", None)
        st.rerun()

def render_worker_reconnect(store, current_session_id: str, session_dir: str):

    if not session_dir or not os.path.isdir(session_dir):
        return
    if st.session_state.get("_worker_reconnect_checked"):
        return

    st.session_state["_worker_reconnect_checked"] = True

    try:
        from utils.run_tracker import find_session_runs, is_pid_alive, write_status
        runs = find_session_runs(session_dir)
    except Exception:
        return

    messages = store.get_messages(current_session_id)

    for run in runs:
        status  = run.get("status", "")
        run_dir = run.get("run_dir", "")
        wf_name = run.get("workflow_name", "workflow")
        if not run_dir:
            continue

        if status in ("pending", "running"):
            pid   = run.get("pid")
            alive = is_pid_alive(pid)

            if alive:
                st.session_state["_watching_worker_run_dir"] = run_dir
                return  
            _stderr_path = os.path.join(run_dir, "worker_stderr.log")
            _stderr_txt  = ""
            try:
                if os.path.isfile(_stderr_path):
                    _stderr_txt = open(_stderr_path, encoding="utf-8",
                                       errors="replace").read().strip()
            except Exception:
                pass

            err_msg = _stderr_txt or "Worker process terminated unexpectedly (no stderr output)."
            try:
                write_status(run_dir, {**run,
                    "status":      "failed",
                    "finished_at": run.get("finished_at") or "",
                    "error":       err_msg,
                })
            except Exception:
                pass

            with st.chat_message("assistant"):
                banner = _("Background pipeline {workflow} stopped (process no longer running).").format(
                    workflow=f"**{wf_name}**"
                )
                st.error(banner)
                if _stderr_txt:
                    with st.expander(_("Worker error log"), expanded=True):
                        st.code(_stderr_txt[-3000:], language="python")
            _restore_failed_run_to_review(run_dir, err_msg)
            st.session_state.pop("_watching_worker_run_dir", None)
            st.rerun()
            return

        if status == "failed":
            already_shown = any(
                (m.get("metadata") or {}).get("worker_run_dir") == run_dir
                for m in messages
            )
            if already_shown:
                continue
            err = run.get("error") or "unknown error"
            fail_msg = _("Pipeline {workflow} failed").format(
                workflow=f"**{wf_name}**"
            )
            fail_msg = f"### {fail_msg}\n\n```\n{err}\n```"
            # Show worker.log snippet so the user can see what happened
            _wlog_path = os.path.join(run_dir, "worker.log")
            _wlog_txt  = ""
            try:
                if os.path.isfile(_wlog_path):
                    _wlog_txt = open(_wlog_path, encoding="utf-8",
                                     errors="replace").read().strip()
            except Exception:
                pass
            store.append_message(current_session_id, "assistant", fail_msg, "",
                                  metadata={"worker_run_dir": run_dir})
            with st.chat_message("assistant"):
                st.error(fail_msg)
                if _wlog_txt:
                    with st.expander(_("Worker log"), expanded=True):
                        st.code(_wlog_txt[-4000:], language=None)
            _restore_failed_run_to_review(run_dir, err)
            st.session_state.pop("_watching_worker_run_dir", None)
            st.rerun()
            continue

        if status != "completed":
            continue

        already_shown = any(
            (m.get("metadata") or {}).get("worker_run_dir") == run_dir
            for m in messages
        )
        if already_shown:
            continue

        plot_paths   = run.get("analysis_images") or []
        valid_imgs   = [p for p in plot_paths if os.path.isfile(p)]
        text_summary = run.get("text_summary") or ""
        warnings     = run.get("warnings") or []
        data_location = run_dir

        import re as _re
        from utils.llm_utils import get_llm_instance

        stats_txt = text_summary[:3000] if text_summary else "{}"
        warn_txt  = "\n".join(warnings) if warnings else "None"

        _prompt = _(COMPLETED_PIPELINE_REPORT_PROMPT).format(
            workflow=wf_name,
            stats=stats_txt,
            warnings=warn_txt,
            data_location=data_location,
        )

        report = ""
        with st.spinner(_("Generating report...")):
            try:
                _raw   = get_llm_instance(is_planner=False).invoke(_prompt)
                report = _raw if isinstance(_raw, str) else _raw.content
                report = _re.sub(r"<think>.*?</think>", "", report, flags=_re.DOTALL).strip()
            except Exception as exc:
                report = (
                    f"### {_('Pipeline Complete')}\n\n{_('Report generation error: {error}').format(error=exc)}"
                )

        with st.chat_message("assistant"):
            banner = _(
                "Pipeline {workflow} completed - results recovered after reconnect"
            ).format(
                workflow=f"**{wf_name}**"
            )
            banner = f"*({banner})*"
            st.info(banner)
            render_final(report, [], valid_imgs, "", show_pdf=True)

        meta = {"analysis_images": valid_imgs, "worker_run_dir": run_dir}
        store.append_message(current_session_id, "assistant", report, "", metadata=meta)
        st.rerun()
        break


def render_completed_if_disconnected(app, store, current_session_id: str,
                                     current_session: dict):

    if st.session_state.get("_agent_bg_result"):
        return

    thread_id = (st.session_state.get("thread_id") or
                 (current_session or {}).get("thread_id"))
    if not thread_id:
        return

    messages = store.get_messages(current_session_id)
    if not messages or messages[-1]["role"] == "assistant":
        return

    if st.session_state.get("_disconnected_checked_tid") == thread_id:
        return
    st.session_state["_disconnected_checked_tid"] = thread_id

    try:
        config = {"configurable": {"thread_id": thread_id}}
        current_state = app.get_state(config)
    except Exception:
        return

    if current_state.next:
        return

    full_response = get_final_from_state(current_state)
    if not full_response:
        return

    _imgs = current_state.values.get("analysis_images", [])
    _zip  = current_state.values.get("workflow_result_zip", "")

    with st.chat_message("assistant"):
        banner = _("The previous task completed while the browser was disconnected. Results have been recovered from the server.")
        st.info(banner)
        render_final(full_response, [], _imgs, _zip, show_pdf=True)

    store.append_message(
        current_session_id, "assistant",
        full_response,
        "",
        metadata={"zip_path": _zip, "analysis_images": _imgs} if _zip or _imgs else None,
    )
    st.session_state.pop("_disconnected_checked_tid", None)
    st.rerun()
