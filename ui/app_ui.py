import streamlit as st
import time
import sys
import os

# 修正Python路径，使其能找到agent_graph模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_graph.graph import create_agent_graph

# streamlit run /home/buguai/project/agent/ui/app_ui.py --server.address 0.0.0.0 --server.port 8501
# 设置页面标题和图标
st.set_page_config(page_title="Bio-Agent 智能分析平台", page_icon="🧬")

st.title("🧬 三代测序分析智能体")
st.markdown("---")

# 初始化会话状态，用于存储聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []


# 初始化 Agent 图（只加载一次模型，节省显存）
@st.cache_resource
def load_agent():
    return create_agent_graph("BioAgent")


with st.spinner("正在加载模型..."):
    app = load_agent()

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 侧边栏用于展示 Agent 的中间逻辑
st.sidebar.title("🧠 Agent 思考过程")
status_container = st.sidebar.empty()

# 用户输入框
if prompt := st.chat_input("请输入你的分析指令..."):
    # 将用户消息加入记录
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 运行 Agent 并展示流程
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        last_event = None

        # 实时流式运行 LangGraph
        for event in app.stream({"input": prompt}):
            last_event = event  # 保存最后一个event
            
            # 在侧边栏显示当前运行的节点
            node_name = list(event.keys())[0]
            status_container.info(f"正在执行节点: {node_name}")

            # 如果进入了 Planner 节点，展示一下规划的参数
            if "planner" in event:
                calls = event["planner"].get("tool_calls", [])
                if calls:
                    st.sidebar.warning(f"规划工具: {calls[0]['tool_name']}")
                    st.sidebar.json(calls[0]['tool_args'])
            
            # ===== 改进：通用方式提取响应内容 =====
            # 遍历event中的所有节点，寻找包含答案的字段
            for node_key, node_data in event.items():
                if isinstance(node_data, dict):
                    # 优先查找标准字段
                    for answer_field in ["final_answer", "answer", "response", "output", "result"]:
                        if answer_field in node_data and node_data[answer_field]:
                            full_response = node_data[answer_field]
                            response_placeholder.markdown(full_response)
                            break

        # 调试输出：如果没有找到答案，显示最后的event结构
        if not full_response and last_event:
            st.sidebar.error("⚠️ 未找到标准答案字段")
            st.sidebar.json({"最后事件": last_event})
            # 尝试从最后一个事件的任何值中提取文本
            for node_key, node_data in last_event.items():
                if isinstance(node_data, dict):
                    for key, value in node_data.items():
                        if isinstance(value, str) and len(value) > 10:
                            full_response = value
                            response_placeholder.markdown(full_response)
                            break

        # 降级处理
        if not full_response:
            full_response = "✅ 任务处理完成"
            response_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})