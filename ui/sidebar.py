import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from storage.file_manager import fmt_size
from configs.i18n_config import DEFAULT_LANG
from configs.i18n_config import SUPPORTED_LANGS
from configs.path_config import USER_QUOTA_BYTES
from configs.tool_config import TOOL_DESCIPTION
from tools.workflow.registry import all_specs
from utils.i18n import _
from utils.auth_cookie import clear_login_state
from utils.file_server import make_download_html, is_running


def switch_session(store, session_id: str):
    session = store.get_session(session_id)
    if not session:
        return
    st.session_state.current_session_id = session_id
    st.session_state.thread_id          = session["thread_id"]
    for key in ("pending_prompt", "ui_mode", "waiting_for_mode",
                "waiting_review", "pending_commands", "resume_decision",
                "review_feedback", "thinking_process", "current_run_dir",
                "review_submitted", "confirming_execute", "last_exec_error",
                "resume_run_dir",
                "waiting_workflow_select", "workflow_select_submitted",
                "workflow_candidates_cached",
                "waiting_nfcore_params_review", "nfcore_params_submitted",
                "nfcore_params_cached", "nfcore_params_edited",
                "waiting_prereq_review", "prereq_review_submitted",
                "prereq_cached_files", "prereq_cached_issues", "prereq_edited_files",
                "prereq_cached_workflow", "prereq_cached_input",
                "waiting_local_prereq_review", "local_prereq_review_submitted",
                "local_prereq_cached_params"):
        st.session_state.pop(key, None)


def render_sidebar(store, fm, user_id, user_uid):
    with st.sidebar:
        st.markdown(f"**👤 {user_id}**")
        if st.button(_("Switch User"), width="stretch"):
            clear_login_state()
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.divider()

        lang_options  = list(SUPPORTED_LANGS.keys())
        lang_labels   = list(SUPPORTED_LANGS.values())
        current_idx   = lang_options.index(st.session_state.get("lang", DEFAULT_LANG))
        selected_label = st.selectbox(
            _("Language"), options=lang_labels, index=current_idx, key="lang_selector"
        )
        selected_lang = lang_options[lang_labels.index(selected_label)]
        if selected_lang != st.session_state.get("lang"):
            st.session_state.lang = selected_lang
            store.set_user_lang(user_id, selected_lang)
            st.rerun()

        st.divider()

        with st.expander(_("🧰 Supported Tools & Pipelines"), expanded=False):
            st.markdown(f"**{_('Tools')}**")
            for t in TOOL_DESCIPTION:
                if t["name"] == "workflow":
                    continue
                st.markdown(f"- **{t['name']}**: {t['short_description']}")

            specs = all_specs()
            nfcore = [s for s in specs if s.type == "nfcore"]
            local  = [s for s in specs if s.type == "local"]

            if nfcore:
                st.markdown(f"**{_('Pipelines')}**")
                for s in nfcore:
                    fmt = " / ".join(s.input_formats) if s.input_formats else ""
                    st.markdown(f"- **{s.display_name}**: {s.description}"
                                + (f"  \n  `{fmt}`" if fmt else ""))

            if local:
                st.markdown(f"**{_('Local Workflows')}**")
                for s in local:
                    fmt = " / ".join(s.input_formats) if s.input_formats else ""
                    st.markdown(f"- **{s.display_name}**: {s.description}"
                                + (f"  \n  `{fmt}`" if fmt else ""))

        st.divider()

        if st.button(_("➕ New Session"), width="stretch"):
            new_sess = store.create_session(
                user_id,
                name=f"{_('Session')} {datetime.now().strftime('%m-%d %H:%M')}",
            )
            switch_session(store, new_sess["session_id"])
            st.rerun()

        st.markdown(f"**{_('Sessions')}**")
        sessions = store.get_user_sessions(user_id)
        _sess_pending = st.session_state.get("_sess_del_pending", "")
        _lang = st.session_state.get("lang", DEFAULT_LANG)
        for sess in sessions:
            is_active = sess["session_id"] == st.session_state.current_session_id
            label     = f"📌 {sess['name']}" if is_active else sess["name"]
            col_btn, col_del = st.columns([5, 1])
            with col_btn:
                if st.button(label, key=f"sess_{sess['session_id']}", width="stretch"):
                    switch_session(store, sess["session_id"])
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{sess['session_id']}"):
                    st.session_state["_sess_del_pending"] = sess["session_id"]
                    st.rerun()
            st.caption(f"  {store.message_count(sess['session_id'])} {_('messages')}")

            if _sess_pending == sess["session_id"]:
                _sdir = fm.session_dir(user_uid, sess["session_id"])
                _sz = 0
                try:
                    for _r, _dirs, _fs in os.walk(_sdir):
                        for _f in _fs:
                            try: _sz += os.path.getsize(os.path.join(_r, _f))
                            except OSError: pass
                except Exception:
                    pass
                _sz_str = (f"{_sz/1024/1024/1024:.1f} GB" if _sz >= 1024**3
                           else f"{_sz/1024/1024:.1f} MB" if _sz >= 1024**2
                           else f"{_sz/1024:.0f} KB")
                _warn = (f"⚠️ 删除「{sess['name']}」将同时清除该会话下**所有文件**（上传文件、运行产物、分析结果，共 {_sz_str}），操作不可撤销。"
                         if _lang != "en_US" else
                         f"⚠️ Deleting **{sess['name']}** will permanently remove all session files (uploads, run products, results — {_sz_str}). This cannot be undone.")
                st.warning(_warn)
                _dc1, _dc2 = st.columns(2)
                if _dc1.button("✓ " + ("确认删除" if _lang != "en_US" else "Delete"),
                               key=f"sess_del_yes_{sess['session_id']}", width="stretch"):
                    thread_id = sess.get("thread_id", "")
                    store.delete_session(sess["session_id"])
                    fm.delete_session_files(user_uid, sess["session_id"])
                    if thread_id:
                        try:
                            from storage.checkpointer import get_checkpointer
                            cp = get_checkpointer()
                            if hasattr(cp, "conn"):
                                cp.conn.execute("DELETE FROM checkpoints WHERE thread_id=?", (thread_id,))
                                cp.conn.execute("DELETE FROM checkpoint_blobs WHERE thread_id=?", (thread_id,))
                                cp.conn.execute("DELETE FROM checkpoint_writes WHERE thread_id=?", (thread_id,))
                                cp.conn.commit()
                        except Exception:
                            pass
                    st.session_state.pop("_sess_del_pending", None)
                    if is_active:
                        st.session_state.current_session_id = None
                    st.rerun()
                if _dc2.button("✗ " + ("取消" if _lang != "en_US" else "Cancel"),
                               key=f"sess_del_no_{sess['session_id']}", width="stretch"):
                    st.session_state.pop("_sess_del_pending", None)
                    st.rerun()

        st.markdown("""<style>
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stDownloadButton"] button,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stBaseButton-secondary"] button,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="baseButton-secondary"] button {
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    aspect-ratio: 1 / 1 !important;
    min-height: 36px !important;
    font-size: 16px !important;
    line-height: 1 !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button p,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] button div {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
</style>""", unsafe_allow_html=True)
        st.divider()
        current_sid  = st.session_state.get("current_session_id", "")
        _session_dir = fm.session_dir(user_uid, current_sid) if current_sid else ""
        _lang        = st.session_state.get("lang", DEFAULT_LANG)
        _copy_help   = "复制 session 上传目录路径" if _lang != "en_US" else "Copy session upload directory path"

        _fc1, _fc2 = st.columns([4, 3])
        _fc1.markdown(f"**{_('📁 File Management')}**")
        with _fc2:
            _b1, _b2 = st.columns(2)
            with _b1:
                if st.button("🔄", key="refresh_files", help=_("Refresh file list"),
                             width="stretch"):
                    st.rerun()
            with _b2:
                if st.button("📋", key="copy_session_path", help=_copy_help,
                             width="stretch"):
                    st.session_state._show_session_path = not st.session_state.get("_show_session_path", False)
        if st.session_state.get("_show_session_path") and _session_dir:
            st.code(_session_dir, language=None)

        _current_run_dir = st.session_state.get("current_run_dir", "")
        if _current_run_dir:
            _rdc1, _rdc2 = st.columns([4, 1])
            _run_label = "上次运行目录" if _lang != "en_US" else "Last run dir"
            _rdc1.caption(f"📂 {_run_label}")
            with _rdc2:
                if st.button("📋", key="copy_run_dir",
                             help=_run_label,
                             width="stretch"):
                    st.session_state._show_run_dir = not st.session_state.get("_show_run_dir", False)
            if st.session_state.get("_show_run_dir"):
                st.code(_current_run_dir, language=None)

        usage = fm.get_usage(user_uid)
        used  = usage["total_bytes"]
        pct   = min(used / USER_QUOTA_BYTES, 1.0) if USER_QUOTA_BYTES > 0 else 0

        breakdown = fm.get_session_breakdown(user_uid, current_sid)
        up_sz  = fmt_size(breakdown["upload_bytes"])
        run_sz = fmt_size(breakdown["run_bytes"])
        st.progress(pct, text=f"{fmt_size(used)} / {fmt_size(USER_QUOTA_BYTES)}")
        st.caption(f"📤 {_('Uploads')}: {up_sz}　　🧬 {_('Run products')}: {run_sz}")

        _upload_help = "建议大文件（>1GB）直接上传到服务器 session 目录" if _lang != "en_US" \
                       else "For large files (>1 GB), upload directly to the server session directory"
        st.caption(_upload_help)
        uploaded = st.file_uploader(
            _("Upload files to current session"),
            accept_multiple_files=True,
            key=f"uploader_{current_sid}",
            label_visibility="collapsed",
        )
        if uploaded:
            if "uploaded_file_keys" not in st.session_state:
                st.session_state.uploaded_file_keys = set()
            new_files = []
            for f in uploaded:
                file_key = f"{f.name}_{f.size}"
                if file_key not in st.session_state.uploaded_file_keys:
                    try:
                        if hasattr(f, "seek"):
                            f.seek(0)
                        size_mb = f.size / (1024 * 1024) if hasattr(f, "size") else 0
                        _spin_msg = (f"Saving {f.name} ({size_mb:.0f} MB)..."
                                     if size_mb > 100 else f"Saving {f.name}...")
                        with st.spinner(_spin_msg):
                            fm.save_file(user_uid, current_sid, f.name, f)
                        st.session_state.uploaded_file_keys.add(file_key)
                        new_files.append(f.name)
                    except Exception as e:
                        st.error(f"Upload failed ({f.name}): {e}")
            if new_files:
                st.success(f"Uploaded: {', '.join(new_files)}")
                st.rerun()

        # pending delete key: "file::<name>" | "clear_files" | "rundir::<name>" | "clear_runs"
        _pdk = f"_sb_pending_del_{current_sid}"
        _pending = st.session_state.get(_pdk, "")

        files = fm.list_session_files(user_uid, current_sid)
        if files:
            st.markdown(f"*{len(files)} {_('files')}*")
            for fi in files:
                _fkey = f"file::{fi['name']}"
                col_name, col_dl, col_del = st.columns([4, 1, 1])
                ext  = os.path.splitext(fi["name"])[1].lower()
                mime = {
                    ".zip": "application/zip",
                    ".pdf": "application/pdf",
                    ".md":  "text/markdown",
                    ".csv": "text/csv",
                    ".tsv": "text/tab-separated-values",
                    ".txt": "text/plain",
                    ".bed": "text/plain",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".html": "text/html",
                }.get(ext, "application/octet-stream")
                if _pending == _fkey:
                    col_name.caption(f"⚠️ {_('Delete')} `{fi['name']}`?")
                    if col_dl.button("✓", key=f"fdel_yes_{current_sid}_{fi['name']}",
                                     width="stretch"):
                        fm.delete_file(user_uid, current_sid, fi["name"])
                        st.session_state.pop(_pdk, None)
                        st.rerun()
                    if col_del.button("✗", key=f"fdel_no_{current_sid}_{fi['name']}",
                                      width="stretch"):
                        st.session_state.pop(_pdk, None)
                        st.rerun()
                else:
                    col_name.caption(f"📄 {fi['name']}  `{fmt_size(fi['size'])}`")
                    with col_dl:
                        if is_running():
                            components.html(make_download_html(fi["path"]), height=36, scrolling=False)
                        else:
                            try:
                                with open(fi["path"], "rb") as _f:
                                    st.download_button(
                                        "⬇", data=_f.read(), file_name=fi["name"], mime=mime,
                                        key=f"fdl_{current_sid}_{fi['name']}",
                                        width="stretch",
                                    )
                            except OSError:
                                st.write("")
                    if col_del.button("✕", key=f"fdel_{current_sid}_{fi['name']}",
                                      width="stretch"):
                        st.session_state[_pdk] = _fkey
                        st.rerun()

            if _pending == "clear_files":
                st.warning(_("Delete all uploaded files?"))
                _cc1, _cc2 = st.columns(2)
                if _cc1.button(_("✓ Confirm"), key=f"clrfiles_yes_{current_sid}",
                               width="stretch"):
                    fm.delete_session_files(user_uid, current_sid)
                    st.session_state.pop(f"uploaded_files_{current_sid}", None)
                    st.session_state.pop(_pdk, None)
                    st.rerun()
                if _cc2.button(_("✗ Cancel"), key=f"clrfiles_no_{current_sid}",
                               width="stretch"):
                    st.session_state.pop(_pdk, None)
                    st.rerun()
            else:
                if st.button(_("🗑 Clear session files"), width="stretch"):
                    st.session_state[_pdk] = "clear_files"
                    st.rerun()

        with st.expander(_("🔗 Link server path"), expanded=False):
            _lang = st.session_state.get("lang", DEFAULT_LANG)
            _ph = "/data/users/xxx/sample.bam 或目录路径" if _lang != "en_US" \
                  else "/data/users/xxx/sample.bam or a directory"
            _path_input = st.text_input(
                _("Server file or directory path"),
                key=f"link_path_input_{current_sid}",
                placeholder=_ph,
                label_visibility="collapsed",
            )
            if st.button(_("Link"), key=f"link_path_btn_{current_sid}",
                         width="stretch"):
                _p = (_path_input or "").strip()
                if not _p:
                    st.warning(_("Please enter a path."))
                elif not os.path.exists(_p):
                    st.error(f"{'路径不存在' if _lang != 'en_US' else 'Path not found'}: `{_p}`")
                elif _session_dir:
                    _link_name = os.path.basename(_p.rstrip("/"))
                    _link_dst  = os.path.join(_session_dir, _link_name)
                    os.makedirs(_session_dir, exist_ok=True)
                    if os.path.lexists(_link_dst):
                        st.info(f"{'已存在' if _lang != 'en_US' else 'Already linked'}: `{_link_name}`")
                    else:
                        os.symlink(_p, _link_dst)
                        st.success(f"{'已链接' if _lang != 'en_US' else 'Linked'}: `{_link_name}` → `{_p}`")
                        st.rerun()

            if _session_dir and os.path.isdir(_session_dir):
                _symlinks = [e for e in os.scandir(_session_dir) if os.path.islink(e.path)]
                if _symlinks:
                    for _sl in _symlinks:
                        _icon = "📁" if os.path.isdir(_sl.path) else "📄"
                        _sc1, _sc2 = st.columns([5, 1])
                        _target = os.readlink(_sl.path)
                        _sc1.caption(f"{_icon} `{_sl.name}` → `{_target}`")
                        if _sc2.button("✕", key=f"unlink_{current_sid}_{_sl.name}",
                                       width="stretch"):
                            os.unlink(_sl.path)
                            st.rerun()

        run_dirs = breakdown["run_dirs"]
        if run_dirs:
            with st.expander(f"{_('🗑 Clean run products')}  ({run_sz})", expanded=False):
                _lang = st.session_state.get("lang", DEFAULT_LANG)
                st.caption(
                    "💡 点击 **▶** 可将该目录设为续跑起点，重新提问时将跳过已完成的步骤"
                    if _lang != "en_US" else
                    "💡 Click **▶** to resume a workflow from this run directory — completed steps will be skipped"
                )
                _resume_locked = st.session_state.get("resume_run_dir", "")

                # Pre-load worker statuses for all run_dirs
                try:
                    from utils.run_tracker import read_status as _read_ws
                    _has_tracker = True
                except ImportError:
                    _has_tracker = False

                def _worker_badge(rd_path: str) -> str:
                    if not _has_tracker:
                        return ""
                    ws = _read_ws(rd_path)
                    if ws is None:
                        return ""
                    s = ws.get("status", "")
                    if s == "running":
                        return " ⏳"
                    if s == "pending":
                        return " 🕐"
                    if s == "completed":
                        return " ✅"
                    if s == "failed":
                        return " ❌"
                    return ""

                for rd in run_dirs:
                    _rkey = f"rundir::{rd['name']}"
                    _rd_full_path = os.path.join(fm.session_dir(user_uid, current_sid), rd["name"])
                    _is_locked = _resume_locked == _rd_full_path
                    col_n, col_r, col_d = st.columns([4, 1, 1])
                    if _pending == _rkey:
                        col_n.caption(f"⚠️ {_('Delete')} `{rd['name']}`?")
                        _rc1, _rc2 = st.columns(2)
                        if _rc1.button("✓", key=f"rddel_yes_{current_sid}_{rd['name']}",
                                       width="stretch"):
                            import shutil, os as _os
                            rpath = _os.path.join(
                                fm.session_dir(user_uid, current_sid), rd["name"]
                            )
                            if _os.path.isdir(rpath):
                                shutil.rmtree(rpath, ignore_errors=True)
                            if _resume_locked == rpath:
                                st.session_state.pop("resume_run_dir", None)
                            st.session_state.pop(_pdk, None)
                            st.rerun()
                        if _rc2.button("✗", key=f"rddel_no_{current_sid}_{rd['name']}",
                                       width="stretch"):
                            st.session_state.pop(_pdk, None)
                            st.rerun()
                    else:
                        _badge = _worker_badge(_rd_full_path)
                        _name_display = f"📌 **{rd['name']}**" if _is_locked else f"📁 {rd['name']}"
                        col_n.caption(f"{_name_display}{_badge}  `{fmt_size(rd['size'])}`")
                        _resume_help = ("取消续跑锁定" if _lang != "en_US" else "Unlock resume") if _is_locked \
                                  else ("设为续跑目录（跳过已完成步骤）" if _lang != "en_US" else "Resume from this dir (skip completed steps)")
                        if col_r.button("📌" if _is_locked else "▶",
                                        key=f"resume_{current_sid}_{rd['name']}",
                                        help=_resume_help,
                                        width="stretch"):
                            if _is_locked:
                                st.session_state.pop("resume_run_dir", None)
                            else:
                                st.session_state.resume_run_dir = _rd_full_path
                            st.rerun()
                        if col_d.button("✕", key=f"rddel_{current_sid}_{rd['name']}",
                                        width="stretch"):
                            st.session_state[_pdk] = _rkey
                            st.rerun()

                if _pending == "clear_runs":
                    st.warning(_("Delete all run products?"))
                    _rc1, _rc2 = st.columns(2)
                    if _rc1.button(_("✓ Confirm"), key=f"clrruns_yes_{current_sid}",
                                   width="stretch"):
                        fm.delete_session_run_dirs(user_uid, current_sid)
                        st.session_state.pop(_pdk, None)
                        st.rerun()
                    if _rc2.button(_("✗ Cancel"), key=f"clrruns_no_{current_sid}",
                                   width="stretch"):
                        st.session_state.pop(_pdk, None)
                        st.rerun()
                else:
                    if st.button(_("🗑 Clean all run products"), width="stretch"):
                        st.session_state[_pdk] = "clear_runs"
                        st.rerun()

        if len(usage["sessions"]) > 1:
            with st.expander(_("Storage by session")):
                for sid, sz in sorted(usage["sessions"].items(),
                                      key=lambda x: x[1], reverse=True):
                    label = f"{sid} ({_('current')})" if sid == current_sid else sid
                    st.caption(f"{label}: {fmt_size(sz)}")
