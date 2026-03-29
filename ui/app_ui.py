import streamlit as st
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_graph.graph import create_agent_graph

try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    def flush_logs():
        return []
    def clear_logs():
        pass

# streamlit run /home/buguai/project/agent/ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
st.set_page_config(page_title="Bio-Agent", page_icon="🧬", layout="wide")

# ===== 侧边栏：会话管理 =====
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = "session_1"
if "sessions" not in st.session_state:
    st.session_state.sessions = {"session_1": []}

with st.sidebar:
    st.title("💬 会话")
    if st.button("➕ 新建会话", use_container_width=True):
        session_id = f"session_{len(st.session_state.sessions) + 1}"
        st.session_state.sessions[session_id] = []
        st.session_state.current_session_id = session_id
        st.rerun()
    st.divider()
    st.markdown("**所有会话**")
    for session_id, msgs in st.session_state.sessions.items():
        session_label = (
            f"📌 {session_id}"
            if session_id == st.session_state.current_session_id
            else f"  {session_id}"
        )
        if st.button(session_label, use_container_width=True, key=f"btn_{session_id}"):
            st.session_state.current_session_id = session_id
            st.rerun()
        st.caption(f"  {len(msgs)} 条消息")

# ===== 主区域 =====
st.title("🧬 Bio-Agent 智能分析平台")
st.markdown("---")

current_messages = st.session_state.sessions.get(st.session_state.current_session_id, [])


@st.cache_resource
def load_agent():
    return create_agent_graph("BioAgent")


with st.spinner("正在加载模型..."):
    app = load_agent()

# ===== 显示历史消息 =====
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        thinking = message.get("thinking", "")
        if thinking and thinking.strip():
            with st.expander("🧠 查看思考过程", expanded=False):
                st.markdown(thinking)

# ===== 初始化所有 UI 状态 =====
defaults = {
    "pending_prompt": None,
    "ui_mode": None,
    "waiting_for_mode": False,
    "thread_id": None,
    "waiting_review": False,
    "pending_commands": [],
    "resume_decision": None,
    "review_feedback": "",
    "thinking_process": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===== 用户输入框 =====
if prompt := st.chat_input("请输入你的分析指令..."):
    st.session_state.pending_prompt = prompt
    st.session_state.ui_mode = None
    st.session_state.waiting_for_mode = True
    st.session_state.thread_id = None
    st.session_state.waiting_review = False
    st.session_state.resume_decision = None
    st.session_state.thinking_process = []
    st.rerun()

# ===== 模式选择 =====
button_slot = st.empty()

if st.session_state.waiting_for_mode and st.session_state.pending_prompt:
    with button_slot.container():
        st.info(f"📝 你的输入：{st.session_state.pending_prompt}")
        st.markdown("**请选择处理方式：**")
        col1, col2, col3 = st.columns(3)
        clicked_mode = None
        if col1.button("💬 对话问答", use_container_width=True):
            clicked_mode = "answer"
        if col2.button("🔧 工具调用", use_container_width=True):
            clicked_mode = "tools"
        if col3.button("🤖 自动判断", use_container_width=True):
            clicked_mode = "auto"

        if clicked_mode:
            button_slot.empty()
            st.session_state.ui_mode = clicked_mode
            st.session_state.waiting_for_mode = False
        else:
            st.stop()


# ===== 工具函数 =====
def render_log(log: str):
    """根据内容渲染不同样式的日志行。"""
    if "✓" in log or "成功" in log:
        st.success(log)
    elif "✗" in log or "失败" in log or "错误" in log:
        st.error(log)
    elif "警告" in log or "Warning" in log:
        st.warning(log)
    else:
        st.text(log)


def stream_events(event_iter, thinking_process: list) -> str:
    """
    消费 app.stream() 生成器，把节点名和日志追加渲染到当前容器（status 内）。
    返回从事件中提取到的 full_response。
    """
    full_response = ""
    for event in event_iter:
        node_name = list(event.keys())[0]
        new_logs = flush_logs()

        thinking_process.append(f"📍 **{node_name}**")
        st.markdown(f"📍 `{node_name}`")
        for log in new_logs:
            render_log(log)

        if isinstance(event.get(node_name), dict):
            for key, val in event[node_name].items():
                if key not in ["final_answer", "answer", "response", "output", "result"]:
                    if isinstance(val, (str, int, float)) and len(str(val)) < 200:
                        thinking_process.append(f"  - {key}: {val}")

        # 顺带提取最终答案（不一定有）
        for node_key, node_data in event.items():
            if isinstance(node_data, dict):
                for field in ["final_answer", "answer", "response", "output", "result"]:
                    if node_data.get(field):
                        full_response = node_data[field]

    return full_response


def render_final(full_response: str, thinking_process: list):
    """
    在 status 外、chat_message 内渲染最终答案 + 思考过程折叠框。
    调用前请确保已经在 st.chat_message 上下文里。
    """
    if thinking_process:
        with st.expander("🧠 查看思考过程", expanded=False):
            st.markdown("\n".join(thinking_process))
    st.markdown(full_response if full_response else "✅ 任务处理完成")


def get_final_from_state(current_state) -> str:
    """从 checkpointer state 里取最终答案，比从 event 流里取更可靠。"""
    for field in ["final_answer", "answer", "response", "output", "result"]:
        val = current_state.values.get(field)
        if val:
            return val
    return ""


# ===== 第一段执行：运行到 executor 前暂停 =====
if st.session_state.pending_prompt and st.session_state.ui_mode and not st.session_state.waiting_review:
    prompt = st.session_state.pending_prompt
    ui_mode = st.session_state.ui_mode

    st.session_state.thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # 清空，防止重复执行
    st.session_state.pending_prompt = None
    st.session_state.ui_mode = None
    st.session_state.waiting_for_mode = False

    current_messages.append({"role": "user", "content": prompt})
    st.session_state.sessions[st.session_state.current_session_id] = current_messages

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_process = []
        clear_logs()

        # status 默认折叠，只放执行日志
        with st.status("🔄 Agent 执行中...", expanded=False) as status:
            full_response = stream_events(
                app.stream({"input": prompt, "user_choice": ui_mode}, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)
        next_nodes = current_state.next

        if "executor" in next_nodes:
            # interrupt_before 触发，等待用户确认
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review = True
            st.session_state.thinking_process = thinking_process
            status.update(label="⏸️ 等待你的确认", state="running")
        else:
            # 正常结束
            status.update(label="✅ 执行完成", state="complete")
            if not full_response:
                full_response = get_final_from_state(current_state)

            # ✅ final_answer 在 status 外面渲染，不会混在日志里
            render_final(full_response, thinking_process)

            current_messages.append({
                "role": "assistant",
                "content": full_response if full_response else "✅ 任务处理完成",
                "thinking": "\n".join(thinking_process),
            })
            st.session_state.sessions[st.session_state.current_session_id] = current_messages

    if st.session_state.waiting_review:
        st.rerun()

# ===== 审查确认框 =====
if st.session_state.waiting_review:
    with st.chat_message("assistant"):
        st.markdown("### 📋 待执行命令，请确认")

        if st.session_state.pending_commands:
            for i, cmd in enumerate(st.session_state.pending_commands, 1):
                st.markdown(f"**步骤 {i}**")
                st.code(cmd, language="bash")
        else:
            st.info("（命令列表为空，请检查参数生成是否正常）")

        st.markdown("---")
        feedback = st.text_input("🔧 修改意见（提交修改时填写）", key="review_feedback")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ 确认执行", use_container_width=True):
                st.session_state.waiting_review = False
                st.session_state.resume_decision = "execute"
                st.rerun()
        with col2:
            if st.button("❌ 取消任务", use_container_width=True):
                st.session_state.waiting_review = False
                st.session_state.resume_decision = "cancel"
                st.rerun()
        with col3:
            if st.button("💬 提交修改", use_container_width=True):
                current_feedback = st.session_state.review_feedback.strip()
                if current_feedback:
                    st.session_state.waiting_review = False
                    # st.session_state.review_feedback = feedback
                    st.session_state.resume_decision = "modify"
                    st.rerun()
                else:
                    st.warning("请先填写修改意见")

# ===== 第二段执行：从断点恢复 =====
if st.session_state.resume_decision and st.session_state.thread_id:
    decision = st.session_state.resume_decision
    st.session_state.resume_decision = None
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    if decision == "cancel":
        app.update_state(config, {"next_node": "end_node"}, as_node="human_reviewer")
    elif decision == "modify":
        app.update_state(
            config,
            {
                "next_node": "param_generator",
                "user_feedback": st.session_state.review_feedback,
            },
            as_node="human_reviewer",
        )
        st.session_state.review_feedback = ""
    # execute：不需要更新 state，LangGraph 从断点直接继续到 executor

    with st.chat_message("assistant"):
        thinking_process = st.session_state.thinking_process or []
        clear_logs()

        with st.status("🔄 继续执行...", expanded=False) as status:
            full_response = stream_events(
                app.stream(None, config=config),
                thinking_process,
            )

        current_state = app.get_state(config)

        # 修改后可能再次暂停在 executor 前
        if "executor" in current_state.next:
            st.session_state.pending_commands = current_state.values.get("pending_commands", [])
            st.session_state.waiting_review = True
            st.session_state.thinking_process = thinking_process
            status.update(label="⏸️ 等待你的确认", state="running")
            st.rerun()

        status.update(label="✅ 执行完成", state="complete")

        if not full_response:
            full_response = get_final_from_state(current_state)

        # ✅ final_answer 在 status 外面渲染
        render_final(full_response, thinking_process)

        current_messages.append({
            "role": "assistant",
            "content": full_response if full_response else "✅ 任务处理完成",
            "thinking": "\n".join(thinking_process),
        })
        st.session_state.sessions[st.session_state.current_session_id] = current_messages
        st.session_state.thinking_process = []