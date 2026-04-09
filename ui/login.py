import streamlit as st
from utils.i18n import _
from configs.i18n_config import DEFAULT_LANG


def render_login(store):
    """如果未登录则渲染登录页并 st.stop()。"""
    if st.session_state.get("user_id"):
        return

    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG

    st.title("🧬 Bio-Agent")
    st.markdown(f"### {_('请输入用户名以继续')}")
    with st.form("login_form"):
        uid = st.text_input(_("用户名"), placeholder=_("例如：alice"))
        pwd = st.text_input("密码", type="password")
        submitted = st.form_submit_button(_("登录"), use_container_width=True)
        if submitted:
            if not uid.strip() or not pwd:
                st.error("请填写用户名和密码。")
            elif not store.verify_login(uid.strip(), pwd):
                st.error("用户名或密码错误。")
            else:
                st.session_state.user_id          = uid.strip()
                st.session_state.user_uid         = store.get_user_uid(uid.strip())
                st.session_state.lang             = store.get_user_lang(uid.strip())
                st.session_state.current_session_id = None
                st.rerun()
    st.stop()
