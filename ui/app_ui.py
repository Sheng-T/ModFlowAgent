import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_graph.graph import create_agent_graph

# 多层级导入保证兼容性
try:
    from utils.ui_logger import flush_logs, clear_logs
except ImportError:
    # 降级：没有 ui_logger 就空操作
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
        session_label = f"📌 {session_id}" if session_id == st.session_state.current_session_id else f"  {session_id}"
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

# 显示聊天历史
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "thinking" in message and message["thinking"]:
            with st.expander("🧠 查看思考过程"):
                st.markdown(message["thinking"])

# ===== 初始化状态 =====
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "ui_mode" not in st.session_state:
    st.session_state.ui_mode = None
if "waiting_for_mode" not in st.session_state:
    st.session_state.waiting_for_mode = False

# ===== 用户输入框 =====
if prompt := st.chat_input("请输入你的分析指令..."):
    st.session_state.pending_prompt = prompt
    st.session_state.ui_mode = None
    st.session_state.waiting_for_mode = True
    st.rerun()

# ===== 用 st.empty() 包裹按钮区，点击后可主动清除 =====
# 关键：button_slot 在每次渲染都在同一位置，可以被 .empty() 清空
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
            # 立刻清空按钮区域，再更新状态
            button_slot.empty()
            st.session_state.ui_mode = clicked_mode
            st.session_state.waiting_for_mode = False
            # 不 rerun，直接往下走执行Agent
        else:
            st.stop()  # 没点按钮就停在这里等待

# ===== 有了prompt和模式，执行Agent =====
if st.session_state.pending_prompt and st.session_state.ui_mode:
    prompt = st.session_state.pending_prompt
    ui_mode = st.session_state.ui_mode

    # 清空状态防止重复执行
    st.session_state.pending_prompt = None
    st.session_state.ui_mode = None
    st.session_state.waiting_for_mode = False

    # 加入聊天记录并显示用户消息
    current_messages.append({"role": "user", "content": prompt})
    st.session_state.sessions[st.session_state.current_session_id] = current_messages
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔄 Agent 执行中...", expanded=True) as status:
            full_response = ""
            thinking_process = []
            execution_steps = 0
            log_display = st.empty()  # 日志显示区域
            all_logs = []

            # 清空之前的日志队列
            clear_logs()

            for event in app.stream({"input": prompt, "user_choice": ui_mode}):
                execution_steps += 1
                node_name = list(event.keys())[0]

                # 读取本轮产生的所有日志
                new_logs = flush_logs()
                all_logs.extend(new_logs)

                # 步骤信息
                thinking_process.append(f"📍 **{node_name}**")

                # 实时更新日志显示
                with log_display.container():
                    st.markdown(f"**[步骤 {execution_steps}]** 📍 `{node_name}`")
                    # 显示本轮新日志
                    for log in new_logs:
                        if "✓" in log or "成功" in log:
                            st.success(log)
                        elif "✗" in log or "失败" in log or "错误" in log:
                            st.error(log)
                        elif "警告" in log or "Warning" in log:
                            st.warning(log)
                        else:
                            st.text(log)

                # 记录节点信息到思考过程
                if isinstance(event.get(node_name), dict):
                    for key, val in event[node_name].items():
                        if key not in ["final_answer", "answer", "response", "output", "result"]:
                            if isinstance(val, (str, int, float)) and len(str(val)) < 200:
                                thinking_process.append(f"  - {key}: {val}")

                # 提取最终答案
                for node_key, node_data in event.items():
                    if isinstance(node_data, dict):
                        for answer_field in ["final_answer", "answer", "response", "output", "result"]:
                            if answer_field in node_data and node_data[answer_field]:
                                full_response = node_data[answer_field]
                                break

            status.update(label="✅ Agent 执行完成", state="complete")

        if thinking_process:
            with st.expander("🧠 查看思考过程", expanded=False):
                st.markdown("\n".join(thinking_process))

        st.divider()
        if not full_response:
            full_response = "✅ 任务处理完成"
        st.markdown("### 📌 最终答案")
        st.markdown(full_response)

        current_messages.append({
            "role": "assistant",
            "content": full_response,
            "thinking": "\n".join(thinking_process) if thinking_process else ""
        })
        st.session_state.sessions[st.session_state.current_session_id] = current_messages