from datetime import datetime

import streamlit as st
from storage.file_manager import fmt_size, file_hash
from configs.i18n_config import SUPPORTED_LANGS
from configs.path_config import USER_QUOTA_BYTES
from configs.tool_config import TOOL_DESCIPTION
from configs.workflow_config import PIPELINE_DESCRIPTIONS
from utils.i18n import _


def switch_session(store, session_id: str):
    """切换到指定会话并重置执行状态。"""
    session = store.get_session(session_id)
    if not session:
        return
    st.session_state.current_session_id = session_id
    st.session_state.thread_id          = session["thread_id"]
    for key in ("pending_prompt", "ui_mode", "waiting_for_mode",
                "waiting_review", "pending_commands", "resume_decision",
                "review_feedback", "thinking_process", "current_run_dir",
                "review_submitted", "confirming_execute", "last_exec_error"):
        st.session_state.pop(key, None)


def render_sidebar(store, fm, user_id, user_uid):
    """渲染完整侧边栏：用户信息 / 语言 / 会话管理 / 文件管理。"""
    with st.sidebar:
        # ── 用户信息 ──────────────────────────────────────────────────────────
        st.markdown(f"**👤 {user_id}**")
        if st.button(_("切换用户"), use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.divider()

        # ── 语言切换 ──────────────────────────────────────────────────────────
        lang_options  = list(SUPPORTED_LANGS.keys())
        lang_labels   = list(SUPPORTED_LANGS.values())
        current_idx   = lang_options.index(st.session_state.get("lang", "zh_CN"))
        selected_label = st.selectbox(
            _("语言"), options=lang_labels, index=current_idx, key="lang_selector"
        )
        selected_lang = lang_options[lang_labels.index(selected_label)]
        if selected_lang != st.session_state.get("lang"):
            st.session_state.lang = selected_lang
            store.set_user_lang(user_id, selected_lang)
            st.rerun()

        st.divider()

        # ── 能力一览 ──────────────────────────────────────────────────────────
        with st.expander(_("🧰 支持的工具与流水线"), expanded=False):
            st.markdown(f"**{_('单步工具')}**")
            for t in TOOL_DESCIPTION:
                if t["name"] == "workflow":
                    continue
                st.markdown(f"- **{t['name']}**")

            st.markdown(f"**{_('分析流水线')}**")
            for name, (desc, inputs) in PIPELINE_DESCRIPTIONS.items():
                st.markdown(f"- **{name}**：{desc}  \n  `{inputs}`")

        st.divider()

        # ── 会话管理 ──────────────────────────────────────────────────────────
        if st.button(_("➕ 新建会话"), use_container_width=True):
            new_sess = store.create_session(
                user_id,
                name=f"{_('会话')} {datetime.now().strftime('%m-%d %H:%M')}",
            )
            switch_session(store, new_sess["session_id"])
            st.rerun()

        st.markdown(f"**{_('会话列表')}**")
        sessions = store.get_user_sessions(user_id)
        for sess in sessions:
            is_active = sess["session_id"] == st.session_state.current_session_id
            label     = f"📌 {sess['name']}" if is_active else sess["name"]
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"sess_{sess['session_id']}", use_container_width=True):
                    switch_session(store, sess["session_id"])
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{sess['session_id']}"):
                    thread_id = sess.get("thread_id", "")
                    # 1. 删数据库记录
                    store.delete_session(sess["session_id"])
                    # 2. 删运行结果目录（保留用户上传文件）
                    fm.delete_session_run_dirs(user_uid, sess["session_id"])
                    # 3. 删 LangGraph checkpoint
                    if thread_id:
                        try:
                            from storage.checkpointer import get_checkpointer
                            cp = get_checkpointer()
                            if hasattr(cp, "conn"):
                                cp.conn.execute(
                                    "DELETE FROM checkpoints WHERE thread_id=?", (thread_id,)
                                )
                                cp.conn.execute(
                                    "DELETE FROM checkpoint_blobs WHERE thread_id=?", (thread_id,)
                                )
                                cp.conn.execute(
                                    "DELETE FROM checkpoint_writes WHERE thread_id=?", (thread_id,)
                                )
                                cp.conn.commit()
                        except Exception:
                            pass
                    if is_active:
                        st.session_state.current_session_id = None
                    st.rerun()
            st.caption(f"  {store.message_count(sess['session_id'])} {_('条消息')}")

        # ── 文件管理 ──────────────────────────────────────────────────────────
        st.divider()
        st.markdown(f"**{_('📁 文件管理')}**")

        usage = fm.get_usage(user_uid)
        used  = usage["total_bytes"]
        pct   = min(used / USER_QUOTA_BYTES, 1.0) if USER_QUOTA_BYTES > 0 else 0
        st.progress(pct, text=f"{fmt_size(used)} / {fmt_size(USER_QUOTA_BYTES)}")

        current_sid = st.session_state.get("current_session_id", "")
        uploaded = st.file_uploader(
            _("上传文件到当前会话"),
            accept_multiple_files=True,
            key=f"uploader_{current_sid}",
            label_visibility="collapsed",
        )
        if uploaded:
            if "uploaded_file_hashes" not in st.session_state:
                st.session_state.uploaded_file_hashes = set()
            new_files = []
            for f in uploaded:
                h = file_hash(f)
                if h not in st.session_state.uploaded_file_hashes:
                    fm.save_file(user_uid, current_sid, f.name, f.read())
                    st.session_state.uploaded_file_hashes.add(h)
                    new_files.append(f.name)
            if new_files:
                st.success(f"Uploaded: {', '.join(new_files)}")

        files = fm.list_session_files(user_uid, current_sid)
        if files:
            st.markdown(f"*{len(files)} {_('个文件')}*")
            for fi in files:
                col_name, col_del = st.columns([5, 1])
                col_name.caption(f"📄 {fi['name']}  `{fmt_size(fi['size'])}`")
                if col_del.button("✕", key=f"fdel_{current_sid}_{fi['name']}"):
                    fm.delete_file(user_uid, current_sid, fi["name"])
                    st.rerun()
            if st.button(_("🗑 清空当前会话文件"), use_container_width=True):
                fm.delete_session_files(user_uid, current_sid)
                st.session_state.pop(f"uploaded_files_{current_sid}", None)
                st.rerun()

        if len(usage["sessions"]) > 1:
            with st.expander(_("各会话占用")):
                for sid, sz in sorted(usage["sessions"].items(),
                                      key=lambda x: x[1], reverse=True):
                    label = f"{sid} ({_('当前')})" if sid == current_sid else sid
                    st.caption(f"{label}: {fmt_size(sz)}")
