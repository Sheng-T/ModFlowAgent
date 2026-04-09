import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime

from agent_graph.graph import create_agent_graph
from storage.session_store import get_session_store
from storage.file_manager import get_file_manager
from configs.auth_config import DEFAULT_USERS
from utils.i18n import _

from ui.login   import render_login
from ui.sidebar import render_sidebar, switch_session
from ui.chat    import (
    render_history, render_mode_selector,
    run_first_segment, render_review, run_second_segment,
)

# streamlit run ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
st.set_page_config(page_title="Bio-Agent", page_icon="🧬", layout="wide")

store = get_session_store()
if "default_users_seeded" not in st.session_state:
    store.seed_default_users(DEFAULT_USERS)
    st.session_state.default_users_seeded = True

# ── 登录 ──────────────────────────────────────────────────────────────────────
render_login(store)

user_id  = st.session_state.user_id
user_uid = st.session_state.get("user_uid") or store.get_user_uid(user_id)
fm       = get_file_manager()

# ── 初始化会话（首次进入或切换用户后）────────────────────────────────────────
if not st.session_state.get("current_session_id"):
    sessions = store.get_user_sessions(user_id)
    if sessions:
        switch_session(store, sessions[0]["session_id"])
    else:
        new_sess = store.create_session(
            user_id,
            name=f"{_('会话')} {datetime.now().strftime('%m-%d %H:%M')}",
        )
        switch_session(store, new_sess["session_id"])

# ── 侧边栏 ────────────────────────────────────────────────────────────────────
render_sidebar(store, fm, user_id, user_uid)

# ── 主区域 ────────────────────────────────────────────────────────────────────
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

render_history(current_messages)

# ── 初始化执行状态 ─────────────────────────────────────────────────────────────
defaults = {
    "pending_prompt":   None,
    "ui_mode":          None,
    "waiting_for_mode": False,
    "waiting_review":   False,
    "pending_commands": [],
    "resume_decision":  None,
    "review_feedback":  "",
    "thinking_process": [],
    "review_submitted":   False,
    "confirming_execute": False,
    "current_run_dir":    None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── 用户输入 ──────────────────────────────────────────────────────────────────
if prompt := st.chat_input(_("请输入你的分析指令...")):
    st.session_state.pending_prompt   = prompt
    st.session_state.ui_mode          = None
    st.session_state.waiting_for_mode = True
    st.session_state.waiting_review     = False
    st.session_state.resume_decision    = None
    st.session_state.review_submitted   = False
    st.session_state.confirming_execute = False
    st.session_state.thinking_process   = []
    st.rerun()

# ── 执行流程 ──────────────────────────────────────────────────────────────────
render_mode_selector()
run_first_segment(app, store, fm, user_uid, current_session_id, current_session)
render_review(app)
run_second_segment(app, store, fm, user_uid, current_session_id)
