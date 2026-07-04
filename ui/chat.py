"""
聊天主区域：消息展示 / 模式选择 / 执行 / 审查。
"""
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


# ── 内部工具 ───────────────────────────────────────────────────────────────────


def _fmt_elapsed(secs: float) -> str:
    s = int(secs)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _parse_progress_log(log: str) -> None:
    """解析 runner 发出的结构化进度标记，更新 session_state._step_progress。"""
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
        # Runner successfully spawned a detached worker — start background polling
        rest = log[len("[WORKER_STARTED]"):].strip()
        for part in rest.split():
            if part.startswith("run_dir="):
                st.session_state["_watching_worker_run_dir"] = part[len("run_dir="):]
                break


def _render_step_progress() -> bool:
    """渲染步骤进度卡片，返回是否有进度数据。"""
    prog = st.session_state.get("_step_progress")
    if not prog or not prog.get("steps"):
        return False

    total       = prog["total"]
    steps       = prog["steps"]
    status_map  = prog["status"]
    elapsed_map = prog["elapsed"]
    start_times = prog["start_times"]
    now         = _time.time()
    lang        = st.session_state.get("lang", "zh_CN")

    done_count = sum(1 for s in status_map.values() if s in ("done", "skip", "failed"))
    fraction   = done_count / total if total > 0 else 0
    label      = f"Step {done_count}/{total}" if lang == "en_US" else f"步骤 {done_count}/{total}"
    st.progress(fraction, text=label)

    for step_name in steps:
        status  = status_map.get(step_name, "pending")
        elapsed = elapsed_map.get(step_name)
        if status == "running":
            elapsed = now - start_times.get(step_name, now)
            icon, note = "⏳", f"  `{_fmt_elapsed(elapsed)}`"
        elif status == "done":
            icon = "✅"
            note = f"  `{_fmt_elapsed(elapsed)}`" if elapsed is not None else ""
        elif status == "skip":
            icon = "⏭"
            note = "  *(resumed)*"
        elif status == "failed":
            icon = "❌"
            note = f"  `{_fmt_elapsed(elapsed)}`" if elapsed is not None else ""
        else:
            icon, note = "⬜", ""
        st.markdown(f"{icon} &nbsp; `{step_name}`{note}")

    return True


def _remove_run_dir(run_dir: str | None) -> None:
    """删除未进入执行阶段的 run_dir（用户在 review 阶段取消时调用）。"""
    if not run_dir or not os.path.isdir(run_dir):
        return
    try:
        import shutil
        shutil.rmtree(run_dir, ignore_errors=True)
    except Exception:
        pass


# ── 渲染工具 ──────────────────────────────────────────────────────────────────

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

def render_log(log: str):
    """渲染单条日志。内部调试前缀的行静默丢弃，只显示关键状态。"""
    stripped = log.strip()
    if not stripped:
        return
    for prefix in _LOG_INTERNAL_PREFIXES:
        if stripped.startswith(prefix):
            return   # 内部日志不显示到 UI

    lower = stripped.lower()
    if "✓" in stripped or "成功" in stripped or "succeeded" in lower or "success" in lower:
        st.success(stripped)
    elif "✗" in stripped or "失败" in stripped or "错误" in stripped or "failed" in lower or "error" in lower:
        st.error(stripped)
    elif "警告" in stripped or "warning" in lower:
        st.warning(stripped)
    else:
        st.text(stripped)


def stream_events(event_iter, thinking_process: list) -> str:
    """
    消费 LangGraph 事件流，同时把 ui_print 日志实时渲染到 Streamlit。
    每个事件到来前先刷一次日志队列（非阻塞），事件处理完再刷一次。
    """
    full_response = ""

    def _flush():
        flush_logs()  # 只清空队列，不渲染到 UI

    for event in event_iter:
        _flush()
        node_name = list(event.keys())[0]
        thinking_process.append(f"📍 **{node_name}**")
        st.markdown(f"📍 `{node_name}`")
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
    """渲染图片轮播：≤2 张用双列网格，>2 张用 prev/next 导航。"""
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
                        label=f"⬇ {os.path.basename(p)}",
                        data=f, file_name=os.path.basename(p),
                        mime="image/png",
                        key=f"dl_img_{_sfx}_{i}",
                        width="stretch",
                    )
        return

    # 超过 2 张：轮播
    key = f"_img_idx_{_sfx}"
    if key not in st.session_state:
        st.session_state[key] = 0
    idx = int(st.session_state.get(key, 0))
    idx = max(0, min(idx, len(imgs) - 1))

    # ── Navigation bar ────────────────────────────────────────────────────────
    name = os.path.basename(imgs[idx])
    col_p, col_info, col_n = st.columns([1, 5, 1])
    with col_p:
        if st.button("◀", key=f"prev_{key}", disabled=(idx == 0), width="stretch"):
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
        if st.button("▶", key=f"next_{key}", disabled=(idx == len(imgs) - 1), width="stretch"):
            st.session_state[key] = idx + 1
            idx = idx + 1

    # Re-read after possible update
    idx = max(0, min(st.session_state.get(key, 0), len(imgs) - 1))
    st.image(imgs[idx], width=680)
    with open(imgs[idx], "rb") as f:
        dl_label = f"⬇ Download {os.path.basename(imgs[idx])}" if lang == "en_US" else f"⬇ 下载 {os.path.basename(imgs[idx])}"
        st.download_button(
            label=dl_label, data=f,
            file_name=os.path.basename(imgs[idx]),
            mime="image/png",
            key=f"dl_carousel_{key}_{idx}",
            width="stretch",
        )

    # 缩略图导航条（点击跳转）
    with st.expander("🖼 " + ("All charts" if lang == "en_US" else "所有图表"), expanded=False):
        thumb_cols = st.columns(min(len(imgs), 4))
        for ti, p in enumerate(imgs):
            with thumb_cols[ti % 4]:
                st.image(p, caption=f"{ti + 1}. {os.path.basename(p)}", width="stretch")
                if st.button(f"{'View' if lang == 'en_US' else '查看'} {ti + 1}",
                             key=f"thumb_{key}_{ti}", width="stretch"):
                    st.session_state[key] = ti


def render_final(full_response: str, thinking_process: list,
                 analysis_images: list | None = None,
                 workflow_result_zip: str = "",
                 show_pdf: bool = True):
    if thinking_process:
        with st.expander(_("🧠 View thinking process"), expanded=False):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else _("✅ Task completed"))

    if analysis_images:
        show_imgs = [p for p in analysis_images if os.path.isfile(p)]
        if show_imgs:
            st.markdown("---")
            lang = get_lang()
            title = "**📊 Analysis Charts**" if lang == "en_US" else "**📊 分析图表**"
            st.markdown(title)
            _render_image_carousel(show_imgs, key_suffix=f"final_{id(analysis_images)}")

    # ── 下载 / 复制区 ──────────────────────────────────────────────────────────
    if full_response or analysis_images or workflow_result_zip:
        lang = get_lang()
        report_text = full_response or ""
        _key_suffix = str(len(report_text))

        st.markdown("---")

        if not show_pdf:
            # Q&A 模式：只显示复制按钮，不生成 PDF
            copy_label = "📋 Copy" if lang == "en_US" else "📋 复制"
            _render_copy_button(report_text, copy_label, key=f"copy_{_key_suffix}")
        else:
            # 结果总结模式：ZIP + MD + PDF
            if workflow_result_zip and os.path.isfile(workflow_result_zip):
                zip_label = "⬇ Download Results (.zip)" if lang == "en_US" else "⬇ 下载结果压缩包 (.zip)"
                _render_zip_download(workflow_result_zip, zip_label)

            col_md, col_pdf = st.columns(2)

            with col_md:
                md_label = "⬇ Download Report (.md)" if lang == "en_US" else "⬇ 下载报告 (.md)"
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
                    pdf_label = "⬇ Download Report (.pdf)" if lang == "en_US" else "⬇ 下载报告 (.pdf)"
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
                    st.caption("PDF unavailable — run `pip install fpdf2`" if lang == "en_US"
                               else "PDF 不可用，请执行 `pip install fpdf2`")
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
    lang = get_lang()

    with st.chat_message("assistant"):
        if lang == "en_US":
            st.markdown("### 📄 Review Sample Sheet")
            st.markdown(
                "The system has auto-generated the samplesheet below. "
                "Please verify that **file paths** (BAM, reference, etc.) are correct before continuing.  \n"
                "You can **edit the content directly** if needed."
            )
        else:
            st.markdown("### 📄 请确认样本表")
            st.markdown(
                "系统已根据上传文件自动生成以下样本表，如有需要可**直接编辑**下方内容，"
                "确认 **文件路径**（BAM、参考基因组等）无误后再继续。"
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
            if lang == "en_US":
                st.info("⚠️ Fix the errors above, then click **Confirm** to re-validate and continue.")
            else:
                st.info("⚠️ 请修正上方错误后点击**确认继续**，系统将重新校验。")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "✅ Confirm & Continue" if lang == "en_US" else "✅ 确认继续",
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
                    # Still has errors after edit — refresh displayed issues
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
                _("❌ Cancel") if lang == "en_US" else "❌ 取消",
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
    lang = get_lang()

    with st.chat_message("assistant"):
        if lang == "en_US":
            st.markdown("### 🔬 Select a Workflow")
            st.markdown("Multiple workflows match your request. Please select one to proceed:")
        else:
            st.markdown("### 🔬 请选择工作流")
            st.markdown("有多个工作流符合您的需求，请选择一个继续：")

        _selector_input = st.session_state.get("workflow_selector_user_input", "")
        if _selector_input:
            from agent_graph.nodes.router.entry import _detect_data_type_mismatch
            _hint = _detect_data_type_mismatch(_selector_input.lower())
            if _hint:
                st.warning(_hint)

        submitted = st.session_state.get("workflow_select_submitted", False)

        if submitted:
            st.info("⏳ Processing..." if lang == "en_US" else "⏳ 处理中，请稍候...")

        for cand in candidates:
            is_recommended = cand.get("recommended", False)
            label = cand.get("display_name") or cand.get("name", "")
            wf_type = cand.get("type", "")
            type_badge = "🔵 nfcore" if wf_type == "nfcore" else "🟢 local"
            reason = cand.get("reason", "")
            rec_label = (" ⭐ " + (_("Recommended") if lang == "en_US" else "推荐")) if is_recommended else ""

            with st.expander(f"{label}  {type_badge}{rec_label}", expanded=is_recommended):
                st.markdown(cand.get("description", ""))
                if reason:
                    st.caption(f"💡 {reason}")
                btn_label = _("✅ Select this") if lang == "en_US" else "✅ 选择此工作流"
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


        with st.status(_("🔄 Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "human_workflow_selector" in current_state.next:
            st.session_state.waiting_workflow_select     = True
            st.session_state.workflow_select_submitted   = False
            st.session_state.thinking_process            = thinking_process
            st.session_state.pop("workflow_candidates_cached", None)
            status.update(label=_("⏸️ Awaiting workflow selection"), state="running")
            st.rerun()
        elif "human_local_prereq_reviewer" in current_state.next:
            st.session_state.waiting_local_prereq_review   = True
            st.session_state.local_prereq_review_submitted = False
            st.session_state.thinking_process             = thinking_process
            st.session_state.pop("local_prereq_cached_params", None)
            st.session_state.pop("local_prereq_edit_resume_dir", None)  # reset so value= default takes effect
            status.update(label=_("⏸️ Awaiting workflow parameters"), state="running")
            st.rerun()
        elif "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_("⏸️ Awaiting samplesheet confirmation"), state="running")
            st.rerun()
        elif "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = current_state.values.get("run_dir", "") or get_run_dir()
            status.update(label=_("⏸️ Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_("✅ Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []


def render_local_prereq_reviewer(app):
    """Render editable local workflow parameters UI when graph is paused before human_local_prereq_reviewer."""
    if not st.session_state.get("waiting_local_prereq_review"):
        return

    from utils.workflow_prerequisites import get_local_prereq_params
    
    # Load local params from graph state only once — cache in session_state
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
    lang = get_lang()

    # Parameter label translations (Chinese → English)
    param_label_translations = {
        "数据文件 (pod5 或 fast5)": "Data File (POD5 or FAST5)",
        "参考序列 FASTA (转录本或基因组，可选)": "Reference FASTA (transcripts or genome, optional)",
        "检测修饰类型 (可选，默认 m6A)": "Modification Type (optional, default m6A)",
        "数据文件 (pod5)": "Data File (POD5)",
        "参考基因组": "Reference Genome",
        "BAM 文件": "BAM File",
    }

    with st.chat_message("assistant"):
        if lang == "en_US":
            st.markdown(f"### 📋 Workflow Parameters: {workflow_name}")
            st.markdown(
                "The system has auto-detected or pre-filled the workflow parameters below. "
                "Please review and **edit any fields** if needed before continuing."
            )
        else:
            st.markdown(f"### 📋 工作流参数：{workflow_name}")
            st.markdown(
                "系统已自动检测或预填以下工作流参数，请检查并根据需要**编辑任何字段**，然后继续。"
            )

        submitted = st.session_state.get("local_prereq_review_submitted", False)
        edited_params = {}
        
        # Organize params in columns for better layout
        for param_def in param_defs:
            key = param_def.get("key", "")
            label = param_def.get("label", key)
            
            # Translate label if in Chinese
            if lang == "en_US" and label in param_label_translations:
                label = param_label_translations[label]
            
            required = param_def.get("required", False)
            param_type = param_def.get("type", "text")
            default_value = param_def.get("default", "")
            current_value = current_params.get(key, default_value)
            help_text = param_def.get("description", "")
            
            # Translate help text if it's common patterns
            if lang == "en_US" and help_text:
                help_translations = {
                    "POD5 格式长读测序文件": "POD5 format long-read sequencing file",
                    "转录本或基因组参考序列（FASTA格式）": "Transcript or genome reference sequence (FASTA format)",
                    "DNA甲基化类型（m5C/m6A等）": "DNA modification type (m5C/m6A, etc.)",
                }
                for zh, en in help_translations.items():
                    if help_text == zh:
                        help_text = en
                        break
            
            # Build label with required indicator — * prefix for required, (optional) suffix for optional
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

        # ── 续跑目录（可选）──────────────────────────────────────────────────
        _resume_label = ("续跑目录 (可选，留空则新建运行目录)"
                         if lang != "en_US"
                         else "Resume from run dir (optional, leave empty to create new)")
        _resume_help = ("填入已有 run_xxx 目录的完整路径，已完成的步骤将自动跳过"
                        if lang != "en_US"
                        else "Full path to an existing run_xxx dir; completed steps will be skipped automatically")
        _resume_default = st.session_state.get("resume_run_dir", "")
        resume_dir_input = st.text_input(
            label=_resume_label,
            value=_resume_default,
            key="local_prereq_edit_resume_dir",
            disabled=submitted,
            help=_resume_help,
        )
        if _resume_default and not submitted:
            st.info(f"{'📌 续跑已锁定：' if lang != 'en_US' else '📌 Resume locked: '}`{_resume_default}`")

        _path_errors_display = st.session_state.get("local_prereq_path_errors", [])
        if _path_errors_display:
            for _err in _path_errors_display:
                st.error(_err)
            if lang == "en_US":
                st.info("Please correct the paths above and click **Confirm & Continue** again.")
            else:
                st.info("请修正上方路径后再次点击 **确认继续**。")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                _("✅ Confirm & Continue") if lang == "en_US" else _("✅ 确认继续"),
                width="stretch", disabled=submitted,
            ):
                import os as _os
                _path_errors: list[str] = []
                for _pdef in param_defs:
                    _k = _pdef.get("key", "")
                    _v = (edited_params.get(_k) or "").strip()
                    _is_path = _pdef.get("type", "path") == "path"
                    if not _is_path:
                        continue
                    _lbl = _pdef.get("label", _k)
                    if _pdef.get("required") and not _v:
                        _path_errors.append(
                            f"**{_lbl}** is required." if lang == "en_US"
                            else f"**{_lbl}** 为必填项。"
                        )
                    elif _v and not _os.path.exists(_v):
                        _path_errors.append(
                            f"**{_lbl}**: path not found — `{_v}`" if lang == "en_US"
                            else f"**{_lbl}**：路径不存在 — `{_v}`"
                        )
                if _path_errors:
                    st.session_state.local_prereq_path_errors = _path_errors
                    st.rerun()
                else:
                    st.session_state.pop("local_prereq_path_errors", None)
                    from utils.user_context import set_run_dir_override, clear_run_dir_override
                    _sid = st.session_state.get("current_session_id", "")
                    _rdir = (resume_dir_input or st.session_state.get("resume_run_dir") or "").strip()
                    if _rdir:
                        set_run_dir_override(_sid, _rdir)
                    else:
                        clear_run_dir_override(_sid)
                    st.session_state.local_prereq_edited_params = edited_params
                    st.session_state.local_prereq_review_submitted = True
                    st.session_state.waiting_local_prereq_review = False
                    st.session_state.pop("local_prereq_cached_params", None)
                    st.rerun()
        with col2:
            if st.button(
                _("❌ Cancel") if lang == "en_US" else _("❌ 取消"),
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
    lang = get_lang()

    with st.chat_message("assistant"):
        if lang == "en_US":
            st.markdown("### 🔬 Select Analysis Type")
            st.markdown("The system is unsure which analysis to run. Please select the appropriate module(s):")
        else:
            st.markdown("### 🔬 请选择分析类型")
            st.markdown("系统无法确定应运行哪种分析，请手动选择合适的模块：")

        if not candidates:
            st.warning("No analysis modules available." if lang == "en_US" else "没有可选的分析模块。")
            if st.button(_("Skip analysis"), key="skip_module_select"):
                st.session_state.waiting_module_select = False
                st.session_state.module_select_submitted = True
                st.session_state.forced_modules = []
                st.rerun()
            return

        submitted = st.session_state.get("module_select_submitted", False)
        selected = st.multiselect(
            _("Select modules") if lang == "en_US" else "选择模块",
            options=candidates,
            default=candidates[:1] if candidates else [],
            key="module_select_choices",
            disabled=submitted,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button(_("✅ Confirm"), width="stretch", disabled=submitted):
                st.session_state.forced_modules = selected
                st.session_state.module_select_submitted = True
                st.session_state.waiting_module_select = False
                st.rerun()
        with col2:
            if st.button(_("⏭ Skip"), width="stretch", disabled=submitted):
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
    # File server unavailable — show server path so user can fetch it manually
    lang = get_lang()
    st.warning("⚠️ 文件服务器未启动，请从服务器路径直接获取文件。" if lang != "en_US"
               else "⚠️ File server unavailable — fetch the file directly from the server path.")
    st.code(zip_path)


def _render_copy_button(text: str, label: str, key: str) -> None:
    """Render a clipboard copy button via JS (base64-encoded to handle all characters)."""
    import base64
    import streamlit.components.v1 as components
    b64 = base64.b64encode(text.encode("utf-8")).decode()
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
                this.textContent='✓ {("Copied" if get_lang() == "en_US" else "已复制")}';
                setTimeout(()=>this.textContent='{label}',2000);
            }});
        ">{label}</button>
        """,
        height=42,
    )


# ── 历史消息 ──────────────────────────────────────────────────────────────────

def _render_history_downloads(meta: dict, content: str):
    """根据已保存的 metadata 恢复历史消息的下载按钮。"""
    lang = get_lang()
    key_base = str(hash(content))[:8]

    zip_path = meta.get("zip_path", "")
    if zip_path and os.path.isfile(zip_path):
        zip_label = "⬇ Download Results (.zip)" if lang == "en_US" else "⬇ 下载结果压缩包 (.zip)"
        _render_zip_download(zip_path, zip_label)

    col_md, col_pdf = st.columns(2)
    md_label  = "⬇ Download Report (.md)"  if lang == "en_US" else "⬇ 下载报告 (.md)"
    pdf_label = "⬇ Download Report (.pdf)" if lang == "en_US" else "⬇ 下载报告 (.pdf)"
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
            pdf_bytes = generate_report_pdf(content, analysis_images, lang)
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
            thinking = message.get("thinking", "")
            if thinking and thinking.strip():
                with st.expander(_("🧠 View thinking process"), expanded=False):
                    st.markdown(thinking)
            meta = message.get("metadata") or {}
            if meta.get("zip_path") or meta.get("analysis_images"):
                hist_imgs = [p for p in (meta.get("analysis_images") or []) if os.path.isfile(p)]
                if hist_imgs:
                    st.markdown("---")
                    lang_h = get_lang()
                    st.markdown("**📊 Analysis Charts**" if lang_h == "en_US" else "**📊 分析图表**")
                    _render_image_carousel(hist_imgs, key_suffix=f"hist_{abs(hash(message['content']))%100000}")
                _render_history_downloads(meta, message["content"])


# ── 模式选择按钮 ──────────────────────────────────────────────────────────────

def render_mode_selector():
    """渲染 4 个模式按钮，返回选中的 mode 字符串或 None。"""
    button_slot = st.empty()
    if not (st.session_state.waiting_for_mode and st.session_state.pending_prompt):
        return
    with button_slot.container():
        st.info(f"📝 {_('Your input')}: {st.session_state.pending_prompt}")
        st.markdown(f"**{_('Select processing mode:')}**")
        col1, col2, col3, col4 = st.columns(4)
        clicked_mode = None
        if col1.button(_("💬 Chat Q&A"),    width="stretch"): clicked_mode = "answer"
        if col2.button(_("🔧 Tool Call"),   width="stretch"): clicked_mode = "tools"
        if col3.button(_("🧬 Pipeline"),    width="stretch"): clicked_mode = "workflow"
        if col4.button(_("🤖 Auto Detect"), width="stretch"): clicked_mode = "auto"
        if clicked_mode:
            button_slot.empty()
            st.session_state.ui_mode          = clicked_mode
            st.session_state.waiting_for_mode = False
        else:
            st.stop()


# ── 第一段执行 ────────────────────────────────────────────────────────────────

def run_first_segment(app, store, fm, user_uid,
                      current_session_id, current_session):
    """运行到 executor 前暂停，返回是否进入 waiting_review。"""
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

        with st.status(_("🔄 Agent running..."), expanded=True) as status:
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
            status.update(label=_("⏸️ Awaiting workflow selection"), state="running")
        elif "human_local_prereq_reviewer" in current_state.next:
            st.session_state.waiting_local_prereq_review   = True
            st.session_state.local_prereq_review_submitted = False
            st.session_state.thinking_process             = thinking_process
            st.session_state.pop("local_prereq_cached_params", None)
            st.session_state.pop("local_prereq_edit_resume_dir", None)  # reset so value= default takes effect
            status.update(label=_("⏸️ Awaiting workflow parameters"), state="running")
        elif "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_("⏸️ Awaiting samplesheet confirmation"), state="running")
        elif "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = current_state.values.get("run_dir", "") or get_run_dir()
            status.update(label=_("⏸️ Awaiting confirmation"), state="running")
        elif "human_module_selector" in current_state.next:
            st.session_state.waiting_module_select  = True
            st.session_state.module_select_submitted = False
            st.session_state.thinking_process       = thinking_process
            status.update(label=_("⏸️ Awaiting module selection"), state="running")
        else:
            status.update(label=_("✅ Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )

    if (st.session_state.waiting_review
            or st.session_state.get("waiting_workflow_select")
            or st.session_state.get("waiting_module_select")
            or st.session_state.get("waiting_prereq_review")
            or st.session_state.get("waiting_local_prereq_review")):
        st.rerun()


# ── 审查确认框 ────────────────────────────────────────────────────────────────

def render_review(app):
    if not st.session_state.waiting_review:
        return

    with st.chat_message("assistant"):
        # 上次执行失败时的错误提示
        last_error = st.session_state.pop("last_exec_error", None)
        if last_error:
            st.error(f"### ❌ {_('Last run failed — commands have been auto-corrected')}")
            with st.expander(_("View error details"), expanded=True):
                st.code(last_error, language="text")
            st.markdown(f"**{_('Review the corrected commands below and confirm to re-run:')}**")
        else:
            st.markdown(f"### 📋 {_('Pending commands — please confirm')}")

        # 前置文件预览（samplesheet 等）
        pre_files = app.get_state(
            {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        ).values.get("pre_files", [])
        if pre_files:
            st.markdown(f"**📄 {_('Pre-requisite files')}**")
            for pf in pre_files:
                with st.expander(f"`{pf['filename']}`", expanded=True):
                    st.code(pf["content"], language="csv")

        if st.session_state.pending_commands:
            st.markdown(f"**💻 {_('Commands to execute')}**")
            for i, cmd in enumerate(st.session_state.pending_commands, 1):
                st.markdown(f"**{_('Step')} {i}**")
                st.code(cmd, language="bash")
        else:
            st.info(_("Command list is empty — check parameter generation"))

        st.markdown("---")
        submitted  = st.session_state.review_submitted
        confirming = st.session_state.get("confirming_execute", False)

        # ── 状态提示（submitted 后显示，按钮仍渲染但全部 disabled）────────────
        if submitted:
            decision = st.session_state.get("resume_decision")
            if decision == "cancel":
                st.warning(_("🚫 Cancelling..."))
            elif decision == "modify":
                st.info(_("🔄 Regenerating commands..."))
            else:
                st.info(_("⏳ Submitted — task is running, please wait..."))

        # ── 操作区（submitted 后全部 disabled，防止重复点击）────────────────
        st.text_input(_("🔧 Revision notes (fill in before submitting)"),
                      key="review_feedback", disabled=submitted)
        col1, col2, col3 = st.columns(3)
        with col1:
            if not confirming:
                if st.button(_("✅ Confirm & Run"),
                             width="stretch", disabled=submitted):
                    st.session_state.confirming_execute = True
                    st.rerun()
            else:
                st.warning(_("⚠️ This will run on the server immediately. Are you sure?"))
                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button(_("▶ Yes, run it"),
                                 width="stretch", type="primary",
                                 disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.session_state.review_submitted   = True
                        st.session_state.resume_decision    = "execute"
                        st.rerun()
                with no_col:
                    if st.button(_("← Let me check again"),
                                 width="stretch", disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.rerun()
        with col2:
            if st.button(_("❌ Cancel"),
                         width="stretch",
                         disabled=submitted or confirming):
                st.session_state.review_submitted = True
                st.session_state.resume_decision  = "cancel"
                st.rerun()
        with col3:
            if st.button(_("💬 Submit Revision"),
                         width="stretch",
                         disabled=submitted or confirming):
                if st.session_state.review_feedback.strip():
                    st.session_state.review_submitted = True
                    st.session_state.resume_decision  = "modify"
                    st.rerun()
                else:
                    st.warning(_("Please fill in revision notes first"))


# ── 本地参数审查恢复段 ───────────────────────────────────────────────────────

def run_local_prereq_review_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user confirms/edits the local workflow parameters."""
    if not (st.session_state.get("local_prereq_review_submitted") and
            st.session_state.get("thread_id")):
        return

    st.session_state.local_prereq_review_submitted = False
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.session_state.pop("local_prereq_review_cancelled", False):
        app.update_state(config, {"next_node": "end_node"}, as_node="human_local_prereq_reviewer")
        st.info(_("✅ Task cancelled"))
        return

    edited_params = st.session_state.pop("local_prereq_edited_params", {})
    if edited_params:
        # Re-sync tool_sequence based on whether reference is now present.
        # generate_local_prereqs_node may have removed samtools_faidx / modkit_pileup
        # when the LLM saw no reference; restore them if user filled one in.
        import tools.workflow.registry as _wf_registry
        current_state_pre = app.get_state(config)
        selected_wf = current_state_pre.values.get("selected_workflow", "")
        spec = _wf_registry.get(selected_wf)
        state_update: dict = {"local_prereq_params": edited_params}
        if spec:
            reference = (edited_params.get("reference") or "").strip()
            _ref_steps = ("samtools_faidx", "modkit_pileup")
            if reference:
                state_update["tool_sequence"] = list(spec.steps)
            else:
                state_update["tool_sequence"] = [s for s in spec.steps if s not in _ref_steps]
        app.update_state(config, state_update, as_node="human_local_prereq_reviewer")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))
        _apply_resume_override(current_session_id)

        with st.status(_("🔄 Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)
            st.session_state.pop("prereq_cached_issues", None)
            status.update(label=_("⏸️ Awaiting samplesheet confirmation"), state="running")
            st.rerun()
        elif "executor" in current_state.next:
            st.session_state.pending_commands  = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review    = True
            st.session_state.review_submitted  = False
            st.session_state.thinking_process  = thinking_process
            st.session_state.current_run_dir   = current_state.values.get("run_dir", "") or get_run_dir()
            status.update(label=_("⏸️ Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_("✅ Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []


# ── prereq 确认恢复段 ─────────────────────────────────────────────────────────

def run_prereq_review_segment(app, store, fm, user_uid, current_session_id):
    """Resume after user confirms/edits the samplesheet."""
    if not (st.session_state.get("prereq_review_submitted") and
            st.session_state.get("thread_id")):
        return

    st.session_state.prereq_review_submitted = False
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if st.session_state.pop("prereq_review_cancelled", False):
        app.update_state(config, {"next_node": "end_node"}, as_node="human_prereq_reviewer")
        st.info(_("✅ Task cancelled"))
        return

    edited_files = st.session_state.pop("prereq_edited_files", [])
    if edited_files:
        app.update_state(config, {"pre_files": edited_files}, as_node="human_prereq_reviewer")

    with st.chat_message("assistant"):
        thinking_process = st.session_state.get("thinking_process") or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))


        with st.status(_("🔄 Agent running..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)

        if "executor" in current_state.next:
            st.session_state.pending_commands  = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review    = True
            st.session_state.review_submitted  = False
            st.session_state.thinking_process  = thinking_process
            st.session_state.current_run_dir   = current_state.values.get("run_dir", "") or get_run_dir()
            status.update(label=_("⏸️ Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_("✅ Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            _imgs = current_state.values.get("analysis_images", [])
            _zip  = current_state.values.get("workflow_result_zip", "")
            _tc   = current_state.values.get("tool_calls", [])
            _show_pdf = bool(_tc or _imgs or _zip)
            render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
                metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
            )
            st.session_state.thinking_process = []


# ── 模块选择恢复段 ────────────────────────────────────────────────────────────

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


        with st.status(_("🔄 Resuming analysis..."), expanded=True) as status:
            full_response = stream_events(app.stream(None, config=config), thinking_process)

        current_state = app.get_state(config)
        status.update(label=_("✅ Completed"), state="complete")
        if not full_response:
            full_response = get_final_from_state(current_state)
        _imgs = current_state.values.get("analysis_images", [])
        _zip  = current_state.values.get("workflow_result_zip", "")
        _tc   = current_state.values.get("tool_calls", [])
        _show_pdf = bool(_tc or _imgs or _zip)
        render_final(full_response, thinking_process, _imgs, _zip, show_pdf=_show_pdf)
        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("✅ Task completed"),
            "\n".join(thinking_process),
            metadata={"zip_path": _zip, "analysis_images": _imgs} if _show_pdf else None,
        )
        st.session_state.thinking_process = []


# ── 后台 agent 线程辅助 ───────────────────────────────────────────────────────

class _AgentResult:
    """线程间传递 app.stream() 结果的容器。"""
    def __init__(self):
        self.events: list = []
        self.done: bool   = False
        self.error        = None


def _run_agent_in_background(app, config, result: _AgentResult,
                             user_uid: int, current_session_id: str,
                             session_dir: str, lang: str = ""):
    """在后台线程里消费 app.stream() 并把事件存入 result.events。"""
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


# ── 第二段执行（断点恢复）────────────────────────────────────────────────────

def run_second_segment(app, store, fm, user_uid, current_session_id):
    # ── 阶段 A：用户刚提交决定，启动后台线程 ─────────────────────────────────
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
            st.info(_("✅ Task cancelled"))
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

    # ── 阶段 B：后台线程运行中或已完成，用 fragment 局部轮询 ──────────────────
    result: _AgentResult = st.session_state.get("_agent_bg_result")
    if result is None:
        return

    @st.fragment(run_every=5)
    def _poll_agent(app, store, current_session_id):
        result: _AgentResult = st.session_state.get("_agent_bg_result")
        if result is None:
            return

        thinking_process = st.session_state.get("_agent_thinking", [])
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        # 把新到的事件和日志追加到累积列表
        while result.events:
            event = result.events.pop(0)
            node_name = list(event.keys())[0]
            thinking_process.append(f"📍 **{node_name}**")
        for log in flush_logs():
            st.session_state.setdefault("_agent_log_buf", []).append(log)
            _parse_progress_log(log)
        st.session_state._agent_thinking = thinking_process

        # 步骤进度（本地工作流专用）
        has_progress = _render_step_progress()

        # 日志折叠框：有进度时默认收起，避免遮挡进度
        log_buf = st.session_state.get("_agent_log_buf", [])
        if log_buf:
            with st.expander(_("📋 Execution log"), expanded=not has_progress):
                st.code("\n".join(log_buf), language=None)

        if not result.done:
            if has_progress:
                # Steps may all be done/skip while summarizer is still running
                prog = st.session_state.get("_step_progress", {})
                all_steps_finished = all(
                    s in ("done", "skip", "failed")
                    for s in prog.get("status", {}).values()
                ) if prog.get("status") else False
                if all_steps_finished:
                    lang = st.session_state.get("lang", "zh_CN")
                    st.info("⏳ 正在分析结果并生成报告，请稍候…" if lang != "en_US"
                            else "⏳ Analyzing results and generating report, please wait…")
            else:
                st.info(_("⏳ Running workflow, please wait..."))
            return

        # 线程已完成，flush 剩余日志
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
                st.session_state.waiting_module_select   = True
                st.session_state.module_select_submitted = False
                st.session_state.thinking_process        = thinking_process
                _cleanup_agent_bg_state()
                st.rerun()

            elif "param_generator" in current_state.next or "executor" in current_state.next:
                history = current_state.values.get("chat_history", [])
                last_error = None
                for msg in reversed(history):
                    content = msg.get("content", "")
                    if msg.get("role") == "assistant" and ("failed" in content.lower() or "失败" in content):
                        last_error = content
                        break
                st.session_state.pending_commands  = current_state.values.get("pending_commands", [])
                st.session_state.waiting_review    = True
                st.session_state.review_submitted  = False
                st.session_state.thinking_process  = thinking_process
                st.session_state.current_run_dir   = current_state.values.get("run_dir", "") or get_run_dir()
                st.session_state.last_exec_error   = last_error
                _cleanup_agent_bg_state()
                st.rerun()

            else:
                full_response = get_final_from_state(current_state)
                _imgs = current_state.values.get("analysis_images", [])
                _zip  = current_state.values.get("workflow_result_zip", "")
                store.append_message(
                    current_session_id, "assistant",
                    full_response if full_response else _("✅ Task completed"),
                    "\n".join(thinking_process),
                    metadata={"zip_path": _zip, "analysis_images": _imgs} if _zip or _imgs else None,
                )
                st.session_state.thinking_process = []
                # If a detached worker was spawned, start watching its run_dir
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
                st.rerun()
        except Exception as e:
            import traceback
            st.error(f"Error processing completed task: {e}\n\n{traceback.format_exc()}")
            _cleanup_agent_bg_state()

    with st.chat_message("assistant"):
        _poll_agent(app, store, current_session_id)


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


def render_worker_poller(store, current_session_id: str):
    """
    若会话中有正在运行的独立 worker（_watching_worker_run_dir 已设置），
    每 10 秒轮询一次 run_status.json。完成后自动生成报告并存入历史。
    """
    watch_dir = st.session_state.get("_watching_worker_run_dir", "")
    if not watch_dir:
        return

    @st.fragment(run_every=10)
    def _poll_worker(store, current_session_id, watch_dir):
        from utils.run_tracker import read_status as _rs
        ws = _rs(watch_dir)
        if ws is None:
            return

        status = ws.get("status", "pending")
        lang   = st.session_state.get("lang", "zh_CN")

        if status in ("pending", "running"):
            total   = ws.get("total_steps", "?")
            current = ws.get("current_step") or "—"
            idx     = ws.get("current_step_index", 0)
            _col_info, _col_cancel = st.columns([5, 1])
            with _col_info:
                if lang == "en_US":
                    st.info(f"⏳ Pipeline running — step {idx+1}/{total}: `{current}`  "
                            f"(refreshes every 10 s)")
                else:
                    st.info(f"⏳ 流水线运行中 — 步骤 {idx+1}/{total}：`{current}`  "
                            f"（每 10 秒自动刷新）")
            with _col_cancel:
                if st.button("⏹ 取消" if lang != "en_US" else "⏹ Cancel",
                             key="cancel_worker_btn", width="stretch"):
                    _pid = ws.get("pid")
                    if _pid:
                        import signal as _sig
                        # Worker was started with start_new_session=True, so it
                        # is the session leader (SID == PID).  Kill the whole
                        # session to reach Singularity/dorado child processes
                        # that may have started their own process groups.
                        _killed = False
                        try:
                            import subprocess as _sp
                            _sp.run(["pkill", "-TERM", "-s", str(_pid)],
                                    capture_output=True)
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
                        "status":      "cancelled",
                        "finished_at": __import__("datetime").datetime.utcnow()
                                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "error":       "Cancelled by user.",
                    })
                    st.session_state.pop("_watching_worker_run_dir", None)
                    st.rerun()
            # 展示运行日志（worker.log = 步骤进度 + 分析器输出）
            _wlog = os.path.join(watch_dir, "worker.log")
            try:
                if os.path.isfile(_wlog):
                    _log_txt = open(_wlog, encoding="utf-8", errors="replace").read().strip()
                    if _log_txt:
                        with st.expander("📋 Worker 运行日志" if lang != "en_US"
                                         else "📋 Worker log", expanded=False):
                            st.code(_log_txt[-4000:], language=None)
            except Exception:
                pass
            # stderr 有内容说明 Python 启动崩溃
            _slog = os.path.join(watch_dir, "worker_stderr.log")
            try:
                if os.path.isfile(_slog):
                    _err_txt = open(_slog, encoding="utf-8", errors="replace").read().strip()
                    if _err_txt:
                        with st.expander("⚠️ Worker 错误日志" if lang != "en_US"
                                         else "⚠️ Worker error log", expanded=True):
                            st.code(_err_txt[-3000:], language="python")
            except Exception:
                pass
            return

        # Terminal state — unregister watcher regardless of outcome
        st.session_state.pop("_watching_worker_run_dir", None)

        if status == "cancelled":
            msg = ("### ⏹ Pipeline cancelled by user."
                   if lang == "en_US" else
                   "### ⏹ 流水线已由用户取消。")
            store.append_message(current_session_id, "assistant", msg, "")
            st.rerun()
            return

        if status == "failed":
            err = ws.get("error", "unknown error")
            msg = (f"### ❌ Pipeline failed\n\n```\n{err}\n```"
                   if lang == "en_US" else
                   f"### ❌ 流水线执行失败\n\n```\n{err}\n```")
            store.append_message(current_session_id, "assistant", msg, "")
            st.rerun()
            return

        if status == "completed":
            # Generate LLM report from persisted analysis data
            plot_paths    = ws.get("analysis_images") or []
            text_summary  = ws.get("text_summary") or ""
            warnings      = ws.get("warnings") or []
            wf_name       = ws.get("workflow_name", "workflow")
            data_location = ws.get("run_dir") or watch_dir
            stats_txt     = text_summary[:3000] if text_summary else "{}"
            warn_txt      = "\n".join(warnings) if warnings else "None"

            import re
            from utils.llm_utils import get_llm_instance

            if lang == "en_US":
                prompt = (
                    f"You are a bioinformatics expert. Summarize the completed {wf_name} "
                    f"pipeline run in a concise Markdown report (3-5 paragraphs).\n\n"
                    f"[Analysis statistics]\n{stats_txt}\n\n"
                    f"[Warnings]\n{warn_txt}\n\n"
                    f"Include: overall result, key metrics, biological interpretation, "
                    f"any warnings. End with: raw results are stored on the server at "
                    f"`{data_location}`."
                )
            else:
                prompt = (
                    f"你是生物信息学专家，请将以下 {wf_name} 流水线的完成结果整理成 "
                    f"简明 Markdown 报告（3-5 段）。\n\n"
                    f"【分析统计】\n{stats_txt}\n\n"
                    f"【警告信息】\n{warn_txt}\n\n"
                    f"包含：总体结论、关键指标、生物学解读、警告事项。"
                    f"末尾注明：原始结果保存在服务器路径 `{data_location}`。"
                )

            with st.spinner("⏳ 生成分析报告…" if lang != "en_US" else "⏳ Generating report…"):
                try:
                    raw    = get_llm_instance(is_planner=False).invoke(prompt)
                    report = raw if isinstance(raw, str) else raw.content
                    report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
                except Exception as exc:
                    report = (f"### ✅ Pipeline Complete\n\nReport generation error: {exc}"
                              if lang == "en_US" else
                              f"### ✅ 流水线已完成\n\n报告生成失败：{exc}")

            valid_imgs = [p for p in plot_paths if os.path.isfile(p)]
            # Always store worker_run_dir so already_shown check works on reconnect.
            meta = {"analysis_images": valid_imgs, "worker_run_dir": data_location}
            store.append_message(current_session_id, "assistant", report, "", metadata=meta)
            # render_final is NOT called here to avoid a one-frame flash.
            # render_history (called during the full rerun below) renders both
            # the report text and the analysis images via the metadata.
            st.rerun()

    with st.chat_message("assistant"):
        _poll_worker(store, current_session_id, watch_dir)


def render_worker_reconnect(store, current_session_id: str, session_dir: str):
    """
    重连检测（后台 worker）：
    - running/pending + PID 存活  → 恢复轮询
    - running/pending + PID 已死  → 标为 failed，显示 stderr 日志
    - completed                   → 自动展示结果（如聊天记录里还没有的话）
    """
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
    lang = st.session_state.get("lang", "zh_CN")

    for run in runs:
        status  = run.get("status", "")
        run_dir = run.get("run_dir", "")
        wf_name = run.get("workflow_name", "workflow")
        if not run_dir:
            continue

        # ── 仍在运行 / 等待 ──────────────────────────────────────────────────
        if status in ("pending", "running"):
            pid   = run.get("pid")
            alive = is_pid_alive(pid)

            if alive:
                # Worker 进程还活着 — 重启轮询
                st.session_state["_watching_worker_run_dir"] = run_dir
                return  # poller 会接管后续展示

            # Worker 已死但状态未更新 — 读 stderr 日志，标为 failed
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
                banner = (f"❌ Background pipeline **{wf_name}** stopped (process no longer running)."
                          if lang == "en_US" else
                          f"❌ 后台流水线 **{wf_name}** 已中断（进程不存在）。")
                st.error(banner)
                if _stderr_txt:
                    with st.expander("Worker 错误日志" if lang != "en_US"
                                     else "Worker error log", expanded=True):
                        st.code(_stderr_txt[-3000:], language="python")
            return

        # ── 失败 ─────────────────────────────────────────────────────────────
        if status == "failed":
            already_shown = any(
                (m.get("metadata") or {}).get("worker_run_dir") == run_dir
                for m in messages
            )
            if already_shown:
                continue
            err = run.get("error") or "unknown error"
            fail_msg = (f"### ❌ Pipeline **{wf_name}** failed\n\n```\n{err}\n```"
                        if lang == "en_US" else
                        f"### ❌ 流水线 **{wf_name}** 执行失败\n\n```\n{err}\n```")
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
                    with st.expander("📋 Worker 运行日志" if lang != "en_US"
                                     else "📋 Worker log", expanded=True):
                        st.code(_wlog_txt[-4000:], language=None)
            continue

        # ── 已完成 ────────────────────────────────────────────────────────────
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

        # ── 生成 LLM 报告（与 poller 路径保持一致）────────────────────────────
        import re as _re
        from utils.llm_utils import get_llm_instance

        stats_txt = text_summary[:3000] if text_summary else "{}"
        warn_txt  = "\n".join(warnings) if warnings else "None"

        if lang == "en_US":
            _prompt = (
                f"You are a bioinformatics expert. Summarize the completed {wf_name} "
                f"pipeline run in a concise Markdown report (3-5 paragraphs).\n\n"
                f"[Analysis statistics]\n{stats_txt}\n\n"
                f"[Warnings]\n{warn_txt}\n\n"
                f"Include: overall result, key metrics, biological interpretation, "
                f"any warnings. End with: raw results are stored on the server at "
                f"`{data_location}`."
            )
        else:
            _prompt = (
                f"你是生物信息学专家，请将以下 {wf_name} 流水线的完成结果整理成 "
                f"简明 Markdown 报告（3-5 段）。\n\n"
                f"【分析统计】\n{stats_txt}\n\n"
                f"【警告信息】\n{warn_txt}\n\n"
                f"包含：总体结论、关键指标、生物学解读、警告事项。"
                f"末尾注明：原始结果保存在服务器路径 `{data_location}`。"
            )

        report = ""
        with st.spinner("⏳ 生成分析报告…" if lang != "en_US" else "⏳ Generating report…"):
            try:
                _raw   = get_llm_instance(is_planner=False).invoke(_prompt)
                report = _raw if isinstance(_raw, str) else _raw.content
                report = _re.sub(r"<think>.*?</think>", "", report, flags=_re.DOTALL).strip()
            except Exception as exc:
                report = (f"### ✅ Pipeline Complete\n\nReport generation error: {exc}"
                          if lang == "en_US" else
                          f"### ✅ 流水线已完成\n\n报告生成失败：{exc}")

        with st.chat_message("assistant"):
            banner = (f"*(Pipeline **{wf_name}** completed — results recovered after reconnect)*"
                      if lang == "en_US" else
                      f"*（流水线 **{wf_name}** 已完成，重连后自动恢复结果）*")
            st.info(banner)
            render_final(report, [], valid_imgs, "", show_pdf=True)

        meta = {"analysis_images": valid_imgs, "worker_run_dir": run_dir}
        store.append_message(current_session_id, "assistant", report, "", metadata=meta)
        st.rerun()
        break


def render_completed_if_disconnected(app, store, current_session_id: str,
                                     current_session: dict):
    """
    重连检测：若后台任务在断连期间已完成但 session_state 已丢失，
    从 LangGraph checkpoint 恢复最终结果并渲染。

    触发条件：
    - 没有活跃后台任务（_agent_bg_result 为 None）
    - 当前 session 有 thread_id
    - 最后一条消息来自用户（说明 assistant 回复尚未保存）
    - LangGraph 图已执行完毕（next 为空）且有最终结果
    """
    if st.session_state.get("_agent_bg_result"):
        return

    # 优先从 session_state 取，其次从 DB 记录取（重连后 session_state 为空）
    thread_id = (st.session_state.get("thread_id") or
                 (current_session or {}).get("thread_id"))
    if not thread_id:
        return

    messages = store.get_messages(current_session_id)
    if not messages or messages[-1]["role"] == "assistant":
        return

    # 防止对同一个 thread 重复检测（已经在本次页面渲染中处理过）
    if st.session_state.get("_disconnected_checked_tid") == thread_id:
        return
    st.session_state["_disconnected_checked_tid"] = thread_id

    try:
        config = {"configurable": {"thread_id": thread_id}}
        current_state = app.get_state(config)
    except Exception:
        return

    # 仍有待执行节点 → 任务还在运行或停在中断点，不处理
    if current_state.next:
        return

    # 图已完成但无内容（全新 thread 或被取消）
    full_response = get_final_from_state(current_state)
    if not full_response:
        return

    lang = st.session_state.get("lang", "zh_CN")
    _imgs = current_state.values.get("analysis_images", [])
    _zip  = current_state.values.get("workflow_result_zip", "")

    with st.chat_message("assistant"):
        banner = ("⚠️ The previous task completed while the browser was disconnected. "
                  "Results have been recovered from the server."
                  if lang == "en_US"
                  else "⚠️ 上次任务在浏览器断连期间已完成，以下为从服务器恢复的结果。")
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
