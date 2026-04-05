import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from agent_graph.graph import create_agent_graph
from storage.session_store import get_session_store
from storage.file_manager import get_file_manager, fmt_size, file_hash
from utils.i18n import _
from configs.i18n_config import SUPPORTED_LANGS
from configs.auth_config import DEFAULT_USERS
from configs.path_config import USER_QUOTA_BYTES

try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    def flush_logs():
        return []
    def clear_logs():
        pass

# streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
st.set_page_config(page_title="Bio-Agent", page_icon="🧬", layout="wide")

store = get_session_store()
# 应用启动时写入默认用户（已存在的用户跳过，不会覆盖密码）
if "default_users_seeded" not in st.session_state:
    print("[SessionStore] 正在初始化默认用户（仅执行一次）...")
    store.seed_default_users(DEFAULT_USERS)
    st.session_state.default_users_seeded = True
    print("[SessionStore] 默认用户初始化完成")

# ─── 登录 ──────────────────────────────────────────────────────────────────────
if "user_id" not in st.session_state or not st.session_state.user_id:
    if "lang" not in st.session_state:
        from configs.i18n_config import DEFAULT_LANG
        st.session_state.lang = DEFAULT_LANG

    st.title("🧬 Bio-Agent")
    st.markdown(f"### {_('请输入用户名以继续')}")
    with st.form("login_form"):
        uid  = st.text_input(_("用户名"), placeholder=_("例如：alice"))
        pwd  = st.text_input("密码", type="password")
        submitted = st.form_submit_button(_("登录"), use_container_width=True)
        if submitted:
            if not uid.strip() or not pwd:
                st.error("请填写用户名和密码。")
            elif not store.verify_login(uid.strip(), pwd):
                st.error("用户名或密码错误。")
            else:
                st.session_state.user_id = uid.strip()
                st.session_state.user_uid = store.get_user_uid(uid.strip())
                st.session_state.lang = store.get_user_lang(uid.strip())
                st.session_state.current_session_id = None
                st.rerun()
    st.stop()

user_id  = st.session_state.user_id
user_uid = st.session_state.get("user_uid") or store.get_user_uid(user_id)
fm = get_file_manager()

# ─── 会话切换时重置执行状态 ───────────────────────────────────────────────────
def _switch_session(session_id: str):
    session = store.get_session(session_id)
    if not session:
        return
    st.session_state.current_session_id = session_id
    st.session_state.thread_id = session["thread_id"]
    for key in ("pending_prompt", "ui_mode", "waiting_for_mode",
                "waiting_review", "pending_commands", "resume_decision",
                "review_feedback", "thinking_process"):
        st.session_state.pop(key, None)

# 首次进入或切换用户后：自动选中最新会话（没有则新建）
if "current_session_id" not in st.session_state or not st.session_state.current_session_id:
    sessions = store.get_user_sessions(user_id)
    if sessions:
        _switch_session(sessions[0]["session_id"])
    else:
        new_sess = store.create_session(
            user_id,
            name=f"{_('会话')} {datetime.now().strftime('%m-%d %H:%M')}",
        )
        _switch_session(new_sess["session_id"])

# ─── 侧边栏 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**👤 {user_id}**")
    if st.button(_("切换用户"), use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.divider()

    # 语言切换
    lang_options = list(SUPPORTED_LANGS.keys())
    lang_labels  = list(SUPPORTED_LANGS.values())
    current_idx  = lang_options.index(st.session_state.get("lang", "zh_CN"))
    selected_label = st.selectbox(
        _("语言"),
        options=lang_labels,
        index=current_idx,
        key="lang_selector",
    )
    selected_lang = lang_options[lang_labels.index(selected_label)]
    if selected_lang != st.session_state.get("lang"):
        st.session_state.lang = selected_lang
        store.set_user_lang(user_id, selected_lang)
        st.rerun()

    st.divider()

    if st.button(_("➕ 新建会话"), use_container_width=True):
        new_sess = store.create_session(
            user_id,
            name=f"{_('会话')} {datetime.now().strftime('%m-%d %H:%M')}",
        )
        _switch_session(new_sess["session_id"])
        st.rerun()

    st.markdown(f"**{_('会话列表')}**")
    sessions = store.get_user_sessions(user_id)
    for sess in sessions:
        is_active = sess["session_id"] == st.session_state.current_session_id
        label = f"📌 {sess['name']}" if is_active else sess["name"]
        col_btn, col_del = st.columns([5, 1])
        with col_btn:
            if st.button(label, key=f"sess_{sess['session_id']}", use_container_width=True):
                _switch_session(sess["session_id"])
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"del_{sess['session_id']}"):
                was_active = is_active
                store.delete_session(sess["session_id"])
                if was_active:
                    st.session_state.current_session_id = None
                st.rerun()
        n = store.message_count(sess["session_id"])
        st.caption(f"  {n} {_('条消息')}")

    # ─── 文件管理 ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("**📁 文件管理**")

    usage = fm.get_usage(user_uid)
    used  = usage["total_bytes"]
    quota = USER_QUOTA_BYTES
    pct   = min(used / quota, 1.0) if quota > 0 else 0
    st.progress(pct, text=f"{fmt_size(used)} / {fmt_size(quota)}")

    # 上传区：绑定到当前 session
    current_sid_for_upload = st.session_state.get("current_session_id", "")
    uploaded = st.file_uploader(
        "上传文件到当前会话",
        accept_multiple_files=True,
        key=f"uploader_{current_sid_for_upload}",
        label_visibility="collapsed",
    )

    if uploaded:
        if "uploaded_file_hashes" not in st.session_state:
            st.session_state.uploaded_file_hashes = set()

        new_files = []

        for f in uploaded:
            h = file_hash(f)

            if h not in st.session_state.uploaded_file_hashes:
                # 新文件才处理
                path = fm.save_file(user_uid, current_sid_for_upload, f.name, f.read())
                st.session_state.uploaded_file_hashes.add(h)
                new_files.append(f.name)

        if new_files:
            st.success(f"已上传：{', '.join(new_files)}")

    # 当前会话文件列表
    files = fm.list_session_files(user_uid, current_sid_for_upload)
    if files:
        st.markdown(f"*当前会话 {len(files)} 个文件*")
        for fi in files:
            col_name, col_del = st.columns([5, 1])
            col_name.caption(f"📄 {fi['name']}  `{fmt_size(fi['size'])}`")
            if col_del.button("✕", key=f"fdel_{current_sid_for_upload}_{fi['name']}"):
                fm.delete_file(user_uid, current_sid_for_upload, fi["name"])
                st.rerun()

        if st.button("🗑 清空当前会话文件", use_container_width=True):
            fm.delete_session_files(user_uid, current_sid_for_upload)
            st.session_state.pop(f"uploaded_files_{current_sid_for_upload}", None)
            st.rerun()

    # 跨会话用量明细（可展开）
    if len(usage["sessions"]) > 1:
        with st.expander("各会话占用"):
            for sid, sz in sorted(usage["sessions"].items(),
                                  key=lambda x: x[1], reverse=True):
                label = sid if sid != current_sid_for_upload else f"{sid} (当前)"
                st.caption(f"{label}: {fmt_size(sz)}")

# ─── 主区域 ────────────────────────────────────────────────────────────────────
st.title(_("🧬 Bio-Agent 智能分析平台"))
st.markdown("---")

current_session_id = st.session_state.current_session_id
current_session    = store.get_session(current_session_id)
current_messages   = store.get_messages(current_session_id)


@st.cache_resource
def load_agent():
    return create_agent_graph("BioAgent")


with st.spinner(_("正在加载模型...")):
    app = load_agent()

# ─── 显示历史消息 ──────────────────────────────────────────────────────────────
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        thinking = message.get("thinking", "")
        if thinking and thinking.strip():
            with st.expander(_("🧠 查看思考过程"), expanded=False):
                st.markdown(thinking)

# ─── 初始化执行状态 ─────────────────────────────────────────────────────────────
defaults = {
    "pending_prompt":   None,
    "ui_mode":          None,
    "waiting_for_mode": False,
    "waiting_review":   False,
    "pending_commands": [],
    "resume_decision":  None,
    "review_feedback":  "",
    "thinking_process": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── 用户输入 ──────────────────────────────────────────────────────────────────
if prompt := st.chat_input(_("请输入你的分析指令...")):
    st.session_state.pending_prompt   = prompt
    st.session_state.ui_mode          = None
    st.session_state.waiting_for_mode = True
    st.session_state.waiting_review   = False
    st.session_state.resume_decision  = None
    st.session_state.thinking_process = []
    st.rerun()

# ─── 模式选择 ──────────────────────────────────────────────────────────────────
button_slot = st.empty()

if st.session_state.waiting_for_mode and st.session_state.pending_prompt:
    with button_slot.container():
        st.info(f"📝 {_('你的输入')}：{st.session_state.pending_prompt}")
        st.markdown(f"**{_('请选择处理方式：')}**")
        col1, col2, col3 = st.columns(3)
        clicked_mode = None
        if col1.button(_("💬 对话问答"), use_container_width=True):
            clicked_mode = "answer"
        if col2.button(_("🔧 工具调用"), use_container_width=True):
            clicked_mode = "tools"
        if col3.button(_("🤖 自动判断"), use_container_width=True):
            clicked_mode = "auto"
        if clicked_mode:
            button_slot.empty()
            st.session_state.ui_mode          = clicked_mode
            st.session_state.waiting_for_mode = False
        else:
            st.stop()


# ─── 工具函数 ──────────────────────────────────────────────────────────────────
def render_log(log: str):
    """根据内容渲染不同样式的日志行。检测逻辑保持原语言中性（图标优先）。"""
    if "✓" in log or "成功" in log or "success" in log.lower():
        st.success(log)
    elif "✗" in log or "失败" in log or "错误" in log or "error" in log.lower():
        st.error(log)
    elif "警告" in log or "Warning" in log or "warning" in log.lower():
        st.warning(log)
    else:
        st.text(log)


def stream_events(event_iter, thinking_process: list) -> str:
    full_response = ""
    for event in event_iter:
        node_name = list(event.keys())[0]
        new_logs  = flush_logs()
        thinking_process.append(f"📍 **{node_name}**")
        st.markdown(f"📍 `{node_name}`")
        for log in new_logs:
            render_log(log)
        if isinstance(event.get(node_name), dict):
            for key, val in event[node_name].items():
                if key not in ["final_answer", "answer", "response", "output", "result"]:
                    if isinstance(val, (str, int, float)) and len(str(val)) < 200:
                        thinking_process.append(f"  - {key}: {val}")
        for _, node_data in event.items():
            if isinstance(node_data, dict):
                for field in ["final_answer", "answer", "response", "output", "result"]:
                    if node_data.get(field):
                        full_response = node_data[field]
    return full_response


def render_final(full_response: str, thinking_process: list):
    if thinking_process:
        with st.expander(_("🧠 查看思考过程"), expanded=False):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else _("✅ 任务处理完成"))


def get_final_from_state(current_state) -> str:
    for field in ["final_answer", "answer", "response", "output", "result"]:
        val = current_state.values.get(field)
        if val:
            return val
    return ""


# ─── 第一段执行：运行到 executor 前暂停 ────────────────────────────────────────
if st.session_state.pending_prompt and st.session_state.ui_mode and not st.session_state.waiting_review:
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

        with st.status(_("🔄 Agent 执行中..."), expanded=False) as status:
            full_response = stream_events(
                app.stream({"input": prompt, "user_choice": ui_mode}, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)
        next_nodes    = current_state.next

        if "executor" in next_nodes:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.thinking_process = thinking_process
            status.update(label=_("⏸️ 等待你的确认"), state="running")
        else:
            status.update(label=_("✅ 执行完成"), state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)
            render_final(full_response, thinking_process)
            store.append_message(
                current_session_id, "assistant",
                full_response if full_response else _("✅ 任务处理完成"),
                "\n".join(thinking_process),
            )

    if st.session_state.waiting_review:
        st.rerun()

# ─── 审查确认框 ─────────────────────────────────────────────────────────────────
if st.session_state.waiting_review:
    with st.chat_message("assistant"):
        st.markdown(f"### 📋 {_('📋 待执行命令，请确认')}")

        if st.session_state.pending_commands:
            for i, cmd in enumerate(st.session_state.pending_commands, 1):
                st.markdown(f"**{_('步骤')} {i}**")
                st.code(cmd, language="bash")
        else:
            st.info(_("命令列表为空，请检查参数生成是否正常"))

        st.markdown("---")
        st.text_input(_("🔧 修改意见（提交修改时填写）"), key="review_feedback")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(_("✅ 确认执行"), use_container_width=True):
                st.session_state.waiting_review  = False
                st.session_state.resume_decision = "execute"
                st.rerun()
        with col2:
            if st.button(_("❌ 取消任务"), use_container_width=True):
                st.session_state.waiting_review  = False
                st.session_state.resume_decision = "cancel"
                st.rerun()
        with col3:
            if st.button(_("💬 提交修改"), use_container_width=True):
                if st.session_state.review_feedback.strip():
                    st.session_state.waiting_review  = False
                    st.session_state.resume_decision = "modify"
                    st.rerun()
                else:
                    st.warning(_("请先填写修改意见"))

# ─── 第二段执行：从断点恢复 ─────────────────────────────────────────────────────
if st.session_state.resume_decision and st.session_state.thread_id:
    decision = st.session_state.resume_decision
    st.session_state.resume_decision = None
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if decision == "cancel":
        app.update_state(config, {"next_node": "end_node"}, as_node="human_reviewer")
    elif decision == "modify":
        app.update_state(
            config,
            {"next_node": "param_generator", "user_feedback": st.session_state.review_feedback},
            as_node="human_reviewer",
        )
        st.session_state.review_feedback = ""

    with st.chat_message("assistant"):
        thinking_process = st.session_state.thinking_process or []
        clear_logs()

        with st.status(_("🔄 继续执行..."), expanded=False) as status:
            full_response = stream_events(
                app.stream(None, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        if "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review   = True
            st.session_state.thinking_process = thinking_process
            status.update(label=_("⏸️ 等待你的确认"), state="running")
            st.rerun()

        status.update(label=_("✅ 执行完成"), state="complete")
        if not full_response:
            full_response = get_final_from_state(current_state)
        render_final(full_response, thinking_process)

        store.append_message(
            current_session_id, "assistant",
            full_response if full_response else _("✅ 任务处理完成"),
            "\n".join(thinking_process),
        )
        st.session_state.thinking_process = []
