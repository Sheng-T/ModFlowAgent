"""
聊天主区域：消息展示 / 模式选择 / 执行 / 审查。
"""
import os
import shutil
import threading
from datetime import datetime

import streamlit as st
from utils.i18n import _
from utils.lang_utils import get_lang
from utils.user_context import get_run_dir, set_session_context

try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    def flush_logs(): return []
    def clear_logs(): pass


# ── 内部工具 ───────────────────────────────────────────────────────────────────



def _remove_run_dir(run_dir: str | None):
    """直接删除 run_dir（执行失败或取消时调用）。"""
    if run_dir and os.path.isdir(run_dir):
        shutil.rmtree(run_dir, ignore_errors=True)
        print(f"[Chat] 运行目录已清理: {run_dir}")


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


def render_final(full_response: str, thinking_process: list,
                 analysis_images: list | None = None,
                 workflow_result_zip: str = ""):
    if thinking_process:
        with st.expander(_("🧠 View thinking process"), expanded=True):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else _("✅ Task completed"))

    if analysis_images:
        st.markdown("---")
        st.markdown(_("**📊 Analyze charts**"))
        # 只展示合并总览图（summary），不展开单张图
        summary_imgs = [p for p in analysis_images if "summary" in os.path.basename(p)]
        show_imgs    = summary_imgs if summary_imgs else analysis_images

        for img_path in show_imgs:
            if os.path.isfile(img_path):
                st.image(img_path, width="stretch")
                with open(img_path, "rb") as f:
                    _dl_label = f"⬇ {_('Download chart')} ({os.path.basename(img_path)})"
                    st.download_button(
                        label=_dl_label,
                        data=f,
                        file_name=os.path.basename(img_path),
                        mime="image/png",
                        key=f"dl_{img_path}",
                    )

    # ── 下载区 ────────────────────────────────────────────────────────────────
    if full_response or analysis_images or workflow_result_zip:
        lang = get_lang()
        report_text = full_response or ""
        _key_suffix = str(len(report_text))

        st.markdown("---")

        # ── Workflow results zip (full width, shown first when present) ───────
        if workflow_result_zip and os.path.isfile(workflow_result_zip):
            zip_label = "⬇ Download Results (.zip)" if lang == "en_US" else "⬇ 下载结果压缩包 (.zip)"
            zip_fname = os.path.basename(workflow_result_zip)
            with open(workflow_result_zip, "rb") as zf:
                st.download_button(
                    label=zip_label,
                    data=zf,
                    file_name=zip_fname,
                    mime="application/zip",
                    key=f"zip_{_key_suffix}",
                    use_container_width=True,
                )

        col_md, col_pdf = st.columns(2)

        # ── Markdown download (always available) ──────────────────────────────
        with col_md:
            md_label = "⬇ Download Report (.md)" if lang == "en_US" else "⬇ 下载报告 (.md)"
            md_fname = f"bio_agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            st.download_button(
                label=md_label,
                data=report_text.encode("utf-8"),
                file_name=md_fname,
                mime="text/markdown",
                key=f"md_{_key_suffix}",
                use_container_width=True,
            )

        # ── PDF download (requires fpdf2) ─────────────────────────────────────
        with col_pdf:
            try:
                from utils.pdf_exporter import generate_report_pdf
                pdf_bytes = generate_report_pdf(report_text, analysis_images or [], lang)
                pdf_label = "⬇ Download Report (.pdf)" if lang == "en_US" else "⬇ 下载报告 (.pdf)"
                pdf_fname = f"bio_agent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.download_button(
                    label=pdf_label,
                    data=pdf_bytes,
                    file_name=pdf_fname,
                    mime="application/pdf",
                    key=f"pdf_{_key_suffix}",
                    use_container_width=True,
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

    # Load pre_files from graph state only once — cache in session_state so reruns
    # don't clobber the text_area values (Streamlit ignores `value` if key already exists).
    if "prereq_cached_files" not in st.session_state:
        config = {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        current_state = app.get_state(config)
        st.session_state.prereq_cached_files = current_state.values.get("pre_files", [])

    pre_files = st.session_state.prereq_cached_files
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

        submitted = st.session_state.get("prereq_review_submitted", False)
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

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "✅ Confirm & Continue" if lang == "en_US" else "✅ 确认继续",
                use_container_width=True, disabled=submitted,
            ):
                st.session_state.prereq_edited_files = edited_files
                st.session_state.prereq_review_submitted = True
                st.session_state.waiting_prereq_review = False
                st.session_state.pop("prereq_cached_files", None)
                st.rerun()
        with col2:
            if st.button(
                _("❌ Cancel") if lang == "en_US" else "❌ 取消",
                use_container_width=True, disabled=submitted,
            ):
                st.session_state.prereq_review_submitted = True
                st.session_state.prereq_review_cancelled = True
                st.session_state.waiting_prereq_review = False
                st.session_state.pop("prereq_cached_files", None)
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
            if st.button(_("✅ Confirm"), use_container_width=True, disabled=submitted):
                st.session_state.forced_modules = selected
                st.session_state.module_select_submitted = True
                st.session_state.waiting_module_select = False
                st.rerun()
        with col2:
            if st.button(_("⏭ Skip"), use_container_width=True, disabled=submitted):
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


# ── 历史消息 ──────────────────────────────────────────────────────────────────

def render_history(messages: list):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            thinking = message.get("thinking", "")
            if thinking and thinking.strip():
                with st.expander(_("🧠 View thinking process"), expanded=True):
                    st.markdown(thinking)


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
        if col1.button(_("💬 Chat Q&A"),    use_container_width=True): clicked_mode = "answer"
        if col2.button(_("🔧 Tool Call"),   use_container_width=True): clicked_mode = "tools"
        if col3.button(_("🧬 Pipeline"),    use_container_width=True): clicked_mode = "workflow"
        if col4.button(_("🤖 Auto Detect"), use_container_width=True): clicked_mode = "auto"
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

        with st.status(_("🔄 Agent running..."), expanded=True) as status:
            full_response = stream_events(
                app.stream({"input": prompt, "user_choice": ui_mode}, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        if "human_prereq_reviewer" in current_state.next:
            st.session_state.waiting_prereq_review   = True
            st.session_state.prereq_review_submitted = False
            st.session_state.thinking_process        = thinking_process
            st.session_state.pop("prereq_cached_files", None)  # clear stale cache from previous run
            status.update(label=_("⏸️ Awaiting samplesheet confirmation"), state="running")
        elif "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = get_run_dir()
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
            render_final(full_response, thinking_process,
                         current_state.values.get("analysis_images", []),
                         current_state.values.get("workflow_result_zip", ""))
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
            )

    if (st.session_state.waiting_review
            or st.session_state.get("waiting_module_select")
            or st.session_state.get("waiting_prereq_review")):
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
                             use_container_width=True, disabled=submitted):
                    st.session_state.confirming_execute = True
                    st.rerun()
            else:
                st.warning(_("⚠️ This will run on the server immediately. Are you sure?"))
                yes_col, no_col = st.columns(2)
                with yes_col:
                    if st.button(_("▶ Yes, run it"),
                                 use_container_width=True, type="primary",
                                 disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.session_state.review_submitted   = True
                        st.session_state.resume_decision    = "execute"
                        st.rerun()
                with no_col:
                    if st.button(_("← Let me check again"),
                                 use_container_width=True, disabled=submitted):
                        st.session_state.confirming_execute = False
                        st.rerun()
        with col2:
            if st.button(_("❌ Cancel"),
                         use_container_width=True,
                         disabled=submitted or confirming):
                st.session_state.review_submitted = True
                st.session_state.resume_decision  = "cancel"
                st.rerun()
        with col3:
            if st.button(_("💬 Submit Revision"),
                         use_container_width=True,
                         disabled=submitted or confirming):
                if st.session_state.review_feedback.strip():
                    st.session_state.review_submitted = True
                    st.session_state.resume_decision  = "modify"
                    st.rerun()
                else:
                    st.warning(_("Please fill in revision notes first"))


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
            st.session_state.current_run_dir   = get_run_dir()
            status.update(label=_("⏸️ Awaiting confirmation"), state="running")
            st.rerun()
        else:
            status.update(label=_("✅ Completed"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            render_final(full_response, thinking_process,
                         current_state.values.get("analysis_images", []),
                         current_state.values.get("workflow_result_zip", ""))
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ Task completed"),
                "\n".join(thinking_process),
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
        render_final(full_response, thinking_process,
                     current_state.values.get("analysis_images", []))
        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("✅ Task completed"),
            "\n".join(thinking_process),
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
                             session_dir: str):
    """在后台线程里消费 app.stream() 并把事件存入 result.events。"""
    try:
        # 为后台线程设置会话上下文
        set_session_context(user_uid, current_session_id, session_dir)
        for event in app.stream(None, config=config):
            result.events.append(event)
    except Exception as e:
        result.error = e
    finally:
        result.done = True


# ── 第二段执行（断点恢复）────────────────────────────────────────────────────

def run_second_segment(app, store, fm, user_uid, current_session_id):
    # ── 阶段 A：用户刚提交决定，启动后台线程 ─────────────────────────────────
    if st.session_state.resume_decision and st.session_state.get("thread_id"):
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

        result = _AgentResult()
        t = threading.Thread(target=_run_agent_in_background,
                             args=(app, config, result, user_uid, current_session_id,
                                   fm.session_dir(user_uid, current_session_id)),
                             daemon=True)
        t.start()
        st.session_state._agent_bg_result    = result
        st.session_state._agent_bg_thread    = t
        st.session_state._agent_thinking     = st.session_state.thinking_process or []
        st.session_state._agent_user_uid     = user_uid
        st.session_state._agent_session_id   = current_session_id
        st.rerun()

    # ── 阶段 B-0：渲染已完成的结果（fragment 外，持久显示）─────────────────────
    # 用 get 而不是 pop，让结果在 session state 中持久保留（下载按钮点击会触发 rerun，
    # 若用 pop 则 rerun 后结果消失，按钮也跟着消失）。
    # 只有新任务开始时（chat_input 提交）才会清除。
    done_result = st.session_state.get("_agent_done_result")
    if done_result:
        with st.chat_message("assistant"):
            render_final(done_result["full_response"], done_result["thinking_process"],
                         done_result["analysis_images"], done_result["workflow_result_zip"])
        return

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
        st.session_state._agent_thinking = thinking_process

        # 日志放进折叠框，不污染主界面
        log_buf = st.session_state.get("_agent_log_buf", [])
        if log_buf:
            with st.expander(_("📋 Execution log"), expanded=True):
                st.code("\n".join(log_buf), language=None)

        if not result.done:
            st.info(_("⏳ Running workflow, please wait..."))
            return

        # 线程已完成，flush 剩余日志
        for log in flush_logs():
            st.session_state.setdefault("_agent_log_buf", []).append(log)

        if result.error:
            st.error(f"Agent error: {result.error}")
            _cleanup_agent_bg_state()
            return

        current_state = app.get_state(config)

        if "human_module_selector" in current_state.next:
            st.session_state.waiting_module_select   = True
            st.session_state.module_select_submitted = False
            st.session_state.thinking_process        = thinking_process
            _cleanup_agent_bg_state()
            st.rerun()
            return

        if "param_generator" in current_state.next or "executor" in current_state.next:
            # 执行失败，返回参数生成器或仍在 executor
            # 无论哪种情况，都要显示错误并回到 review 让用户修改
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
            st.session_state.current_run_dir   = get_run_dir()
            st.session_state.last_exec_error   = last_error
            _cleanup_agent_bg_state()
            st.rerun()
            return

        full_response = get_final_from_state(current_state)
        st.session_state._agent_done_result = {
            "full_response": full_response,
            "thinking_process": thinking_process,
            "analysis_images": current_state.values.get("analysis_images", []),
            "workflow_result_zip": current_state.values.get("workflow_result_zip", ""),
        }
        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("✅ Task completed"),
            "\n".join(thinking_process),
        )
        st.session_state.thinking_process = []
        st.session_state.pop("current_run_dir", None)
        _cleanup_agent_bg_state()
        st.rerun()

    with st.chat_message("assistant"):
        _poll_agent(app, store, current_session_id)


def _cleanup_agent_bg_state():
    for key in ("_agent_bg_result", "_agent_bg_thread", "_agent_thinking",
                "_agent_user_uid", "_agent_session_id", "_agent_log_buf"):
        st.session_state.pop(key, None)
