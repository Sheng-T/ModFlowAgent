import os
import streamlit as st
from configs.i18n_config import DEFAULT_LANG


def _load_css(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "static", "css", filename)
    with open(path, encoding="utf-8") as f:
        return f"<style>{f.read()}</style>"


def render_login(store):
    """Render login page if not authenticated, then st.stop()."""
    if st.session_state.get("user_id"):
        return

    if "lang" not in st.session_state:
        st.session_state.lang = DEFAULT_LANG

    st.markdown(_load_css("login.css"), unsafe_allow_html=True)

    # vertical centering spacer
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        # brand header (pure HTML — renders reliably inside the column)
        st.markdown(
            """
            <div class="brand-icon">🧬</div>
            <div class="brand-title">Bio-Agent</div>
            <div class="brand-sub">Intelligent Nanopore Sequencing Analysis Platform</div>
            <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:.8rem 0 1.4rem"/>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            uid = st.text_input("Username", placeholder="Enter your username")
            pwd = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not uid.strip() or not pwd:
                    st.error("Please enter both username and password.")
                elif not store.verify_login(uid.strip(), pwd):
                    st.error("Invalid username or password.")
                else:
                    st.session_state.user_id            = uid.strip()
                    st.session_state.user_uid           = store.get_user_uid(uid.strip())
                    st.session_state.lang               = store.get_user_lang(uid.strip())
                    st.session_state.current_session_id = None
                    st.rerun()

        st.markdown(
            '<div class="login-footer">Powered by LangGraph · Streamlit</div>',
            unsafe_allow_html=True,
        )

    st.stop()
