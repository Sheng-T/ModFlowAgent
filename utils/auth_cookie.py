"""Cookie-based login persistence with session_state caching."""
from datetime import datetime, timedelta

import streamlit as st

_COOKIE_KEY      = "agent_uid"
_CM_KEY          = "_auth_cookie_manager"
_CM_STATE_KEY    = "_modflowagent_cm_instance"
_COOKIE_INIT_KEY = "_modflowagent_cookie_init_done"
_EXPIRY_DAYS     = 30


def get_cookie_manager():
    """Return cached CookieManager (one per session)."""
    try:
        import extra_streamlit_components as stx
        if _CM_STATE_KEY not in st.session_state:
            st.session_state[_CM_STATE_KEY] = stx.CookieManager(key=_CM_KEY)
        return st.session_state[_CM_STATE_KEY]
    except ImportError:
        return None


def save_login_cookie(user_id: str) -> None:
    mgr = get_cookie_manager()
    if mgr is None:
        return
    try:
        mgr.set(_COOKIE_KEY, user_id,
                expires_at=datetime.now() + timedelta(days=_EXPIRY_DAYS))
    except Exception as e:
        print(f"[Cookie] Failed to save login cookie: {e}")


def clear_login_cookie() -> None:
    mgr = get_cookie_manager()
    if mgr is None:
        return
    try:
        mgr.delete(_COOKIE_KEY)
    except Exception as e:
        print(f"[Cookie] Failed to clear login cookie: {e}")


def clear_login_state() -> None:
    """Clear both cookie and Streamlit session login state."""
    clear_login_cookie()
    for key in ["user_id", "user_uid", "lang", "current_session_id"]:
        st.session_state.pop(key, None)


def restore_from_cookie(store) -> bool:
    """Restore login state from cookie. Returns True if restored."""
    if st.session_state.get("user_id"):
        return True

    mgr = get_cookie_manager()
    if mgr is None:
        return False

    if not st.session_state.get(_COOKIE_INIT_KEY):
        st.session_state[_COOKIE_INIT_KEY] = True
        st.rerun()

    try:
        saved_uid = mgr.get(cookie=_COOKIE_KEY)
    except Exception as e:
        print(f"[Cookie] Failed to restore: {e}")
        return False

    if not saved_uid:
        return False

    user_uid = store.get_user_uid(saved_uid)
    if not user_uid:
        clear_login_cookie()
        return False

    st.session_state.user_id            = saved_uid
    st.session_state.user_uid           = user_uid
    st.session_state.lang               = store.get_user_lang(saved_uid)
    st.session_state.current_session_id = None
    return True
