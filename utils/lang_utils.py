from configs.i18n_config import DEFAULT_LANG


def get_lang() -> str:
    """Get current UI language.

    In Streamlit main thread: reads from st.session_state.
    In background threads (LangGraph nodes): reads from thread-local storage
    set by set_session_context(), avoiding ScriptRunContext warnings.
    """
    # Check thread-local first — set by set_session_context() before background thread starts.
    # This avoids accessing st.session_state from non-Streamlit threads.
    try:
        from utils.user_context import get_thread_lang
        tl = get_thread_lang()
        if tl:
            return tl
    except Exception:
        pass

    # Streamlit main thread path
    try:
        import streamlit as st
        return st.session_state.get("lang", DEFAULT_LANG)
    except Exception:
        return DEFAULT_LANG
