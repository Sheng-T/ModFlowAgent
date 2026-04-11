"""
聊天主区域：消息展示 / 模式选择 / 执行 / 审查。
"""
import os
import shutil

import streamlit as st
from utils.i18n import _
from utils.user_context import get_run_dir, get_session_dir, set_session_context

try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    def flush_logs(): return []
    def clear_logs(): pass


# ── 内部工具 ───────────────────────────────────────────────────────────────────

def _mask_cmd(cmd: str) -> str:
    """Replace absolute server paths with user-friendly placeholders."""
    from utils.lang_utils import get_lang
    lang = get_lang()
    run_dir     = get_run_dir()
    session_dir = get_session_dir()
    if run_dir:
        cmd = cmd.replace(run_dir, "[output dir]" if lang == "en_US" else "[输出目录]")
    if session_dir:
        cmd = cmd.replace(session_dir, "[upload dir]" if lang == "en_US" else "[上传目录]")
    return cmd


def _remove_run_dir(run_dir: str | None):
    """直接删除 run_dir（执行失败或取消时调用）。"""
    if run_dir and os.path.isdir(run_dir):
        shutil.rmtree(run_dir, ignore_errors=True)
        print(f"[Chat] 运行目录已清理: {run_dir}")


# ── 渲染工具 ──────────────────────────────────────────────────────────────────

def render_log(log: str):
    lower = log.lower()
    if "✓" in log or "成功" in log or "succeeded" in lower or "success" in lower:
        st.success(log)
    elif "✗" in log or "失败" in log or "错误" in log or "failed" in lower or "error" in lower:
        st.error(log)
    elif "警告" in log or "warning" in lower:
        st.warning(log)
    else:
        st.text(log)


def stream_events(event_iter, thinking_process: list) -> str:
    full_response = ""
    for event in event_iter:
        node_name = list(event.keys())[0]
        thinking_process.append(f"📍 **{node_name}**")
        st.markdown(f"📍 `{node_name}`")
        for log in flush_logs():
            render_log(log)
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
    return full_response


def render_final(full_response: str, thinking_process: list,
                 analysis_images: list | None = None):
    if thinking_process:
        with st.expander(_("🧠 查看思考过程"), expanded=False):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else _("✅ 任务处理完成"))

    if analysis_images:
        st.markdown("---")
        st.markdown("**📊 分析图表**")
        # 只展示合并总览图（summary），不展开单张图
        summary_imgs = [p for p in analysis_images if "summary" in os.path.basename(p)]
        show_imgs    = summary_imgs if summary_imgs else analysis_images

        for img_path in show_imgs:
            if os.path.isfile(img_path):
                st.image(img_path, width="stretch")
                with open(img_path, "rb") as f:
                    st.download_button(
                        label=f"⬇ {_('下载图表')} ({os.path.basename(img_path)})",
                        data=f,
                        file_name=os.path.basename(img_path),
                        mime="image/png",
                        key=f"dl_{img_path}",
                    )


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
                with st.expander(_("🧠 查看思考过程"), expanded=False):
                    st.markdown(thinking)


# ── 模式选择按钮 ──────────────────────────────────────────────────────────────

def render_mode_selector():
    """渲染 4 个模式按钮，返回选中的 mode 字符串或 None。"""
    button_slot = st.empty()
    if not (st.session_state.waiting_for_mode and st.session_state.pending_prompt):
        return
    with button_slot.container():
        st.info(f"📝 {_('你的输入')}：{st.session_state.pending_prompt}")
        st.markdown(f"**{_('请选择处理方式：')}**")
        col1, col2, col3, col4 = st.columns(4)
        clicked_mode = None
        if col1.button(_("💬 对话问答"), use_container_width=True): clicked_mode = "answer"
        if col2.button(_("🔧 工具调用"), use_container_width=True): clicked_mode = "tools"
        if col3.button(_("🧬 流水线"),   use_container_width=True): clicked_mode = "workflow"
        if col4.button(_("🤖 自动判断"), use_container_width=True): clicked_mode = "auto"
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

        with st.status(_("🔄 Agent 执行中..."), expanded=False) as status:
            full_response = stream_events(
                app.stream({"input": prompt, "user_choice": ui_mode}, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        if "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.review_submitted = False
            st.session_state.thinking_process = thinking_process
            st.session_state.current_run_dir  = get_run_dir()   # 保存供取消时清理
            status.update(label=_("⏸️ 等待你的确认"), state="running")
        else:
            status.update(label=_("✅ 执行完成"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            render_final(full_response, thinking_process,
                         current_state.values.get("analysis_images", []))
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ 任务处理完成"),
                "\n".join(thinking_process),
            )

    if st.session_state.waiting_review:
        st.rerun()


# ── 审查确认框 ────────────────────────────────────────────────────────────────

def render_review(app):
    if not st.session_state.waiting_review:
        return

    with st.chat_message("assistant"):
        # 上次执行失败时的错误提示
        last_error = st.session_state.pop("last_exec_error", None)
        if last_error:
            st.error(f"### ❌ {_('上次执行失败，系统已自动修正命令')}")
            with st.expander(_("查看错误详情"), expanded=False):
                st.code(last_error, language="text")
            st.markdown(f"**{_('请检查以下修正后的命令，确认无误后重新执行：')}**")
        else:
            st.markdown(f"### 📋 {_('待执行命令，请确认')}")

        # 前置文件预览（samplesheet 等）
        pre_files = app.get_state(
            {"configurable": {"thread_id": st.session_state.get("thread_id", "")}}
        ).values.get("pre_files", [])
        if pre_files:
            st.markdown(f"**📄 {_('前置文件')}**")
            for pf in pre_files:
                with st.expander(f"`{pf['filename']}`", expanded=True):
                    st.code(pf["content"], language="csv")

        if st.session_state.pending_commands:
            st.markdown(f"**💻 {_('待执行命令')}**")
            for i, cmd in enumerate(st.session_state.pending_commands, 1):
                st.markdown(f"**{_('步骤')} {i}**")
                st.code(_mask_cmd(cmd), language="bash")
        else:
            st.info(_("命令列表为空，请检查参数生成是否正常"))

        st.markdown("---")
        submitted  = st.session_state.review_submitted
        confirming = st.session_state.get("confirming_execute", False)

        if submitted:
            decision = st.session_state.get("resume_decision")
            if decision == "cancel":
                st.warning(_("🚫 正在取消任务..."))
            elif decision == "modify":
                st.info(_("🔄 正在重新生成命令..."))
            else:
                st.info(_("⏳ 已提交，任务执行中，请稍候..."))
        else:
            st.text_input(_("🔧 修改意见（提交修改时填写）"), key="review_feedback")
            col1, col2, col3 = st.columns(3)
            with col1:
                if not confirming:
                    if st.button(_("✅ 确认执行"), use_container_width=True):
                        st.session_state.confirming_execute = True
                        st.rerun()
                else:
                    st.warning(_("⚠️ 命令将立即在服务器执行，确定吗？"))
                    yes_col, no_col = st.columns(2)
                    with yes_col:
                        if st.button(_("▶ 确定执行"), use_container_width=True, type="primary"):
                            st.session_state.confirming_execute = False
                            st.session_state.review_submitted   = True
                            st.session_state.resume_decision    = "execute"
                            st.rerun()
                    with no_col:
                        if st.button(_("← 我再看看"), use_container_width=True):
                            st.session_state.confirming_execute = False
                            st.rerun()
            with col2:
                if st.button(_("❌ 取消任务"), use_container_width=True, disabled=confirming):
                    st.session_state.review_submitted = True
                    st.session_state.resume_decision  = "cancel"
                    st.rerun()
            with col3:
                if st.button(_("💬 提交修改"), use_container_width=True, disabled=confirming):
                    if st.session_state.review_feedback.strip():
                        st.session_state.review_submitted = True
                        st.session_state.resume_decision  = "modify"
                        st.rerun()
                    else:
                        st.warning(_("请先填写修改意见"))


# ── 第二段执行（断点恢复）────────────────────────────────────────────────────

def run_second_segment(app, store, fm, user_uid,
                       current_session_id):
    if not (st.session_state.resume_decision and st.session_state.get("thread_id")):
        return

    decision = st.session_state.resume_decision
    st.session_state.resume_decision  = None
    st.session_state.waiting_review   = False  # 此处统一关闭，render_review 已显示 ⏳
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if decision == "cancel":
        app.update_state(config, {"next_node": "end_node"}, as_node="human_reviewer")
        # 清理还未执行的 run_dir
        _remove_run_dir(st.session_state.pop("current_run_dir", None))
        st.info(_("✅ 任务已取消"))
        return

    if decision == "modify":
        app.update_state(
            config,
            {"next_node": "param_generator",
             "user_feedback": st.session_state.review_feedback},
            as_node="human_reviewer",
        )
        st.session_state.review_feedback = ""

    with st.chat_message("assistant"):
        thinking_process = st.session_state.thinking_process or []
        clear_logs()
        set_session_context(user_uid, current_session_id,
                            fm.session_dir(user_uid, current_session_id))

        with st.status(_("🔄 继续执行..."), expanded=False) as status:
            full_response = stream_events(
                app.stream(None, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        if "executor" in current_state.next:
            # 检测是否是执行失败后的重试：从 chat_history 里找最后一条含"失败"的 assistant 消息
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
            if last_error:
                status.update(label=_("❌ 执行失败，已自动修正命令，请重新确认"), state="error")
            else:
                status.update(label=_("⏸️ 等待你的确认"), state="running")
            st.rerun()

        status.update(label=_("✅ 执行完成"), state="complete")
        if not full_response:
            full_response = get_final_from_state(current_state)
        render_final(full_response, thinking_process,
                     current_state.values.get("analysis_images", []))
        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("✅ 任务处理完成"),
            "\n".join(thinking_process),
        )
        st.session_state.thinking_process = []
        st.session_state.pop("current_run_dir", None)
