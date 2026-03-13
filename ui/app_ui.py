import streamlit as st
import time
from agent_graph.graph import create_agent_graph

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

        # 实时流式运行 LangGraph
        for event in app.stream({"input": prompt}):
            # 在侧边栏显示当前运行的节点
            node_name = list(event.keys())[0]
            status_container.info(f"正在执行节点: {node_name}")

            # 如果进入了 Planner 节点，展示一下规划的参数
            if "planner" in event:
                calls = event["planner"].get("tool_calls", [])
                if calls:
                    st.sidebar.warning(f"规划工具: {calls[0]['tool_name']}")
                    st.sidebar.json(calls[0]['tool_args'])

            # 这里的逻辑需要根据你 graph 最终输出结果的字段来定
            # 假设最终结果在 summarizer 节点的 final_answer 中
            if "summarizer" in event:
                full_response = event["summarizer"].get("final_answer", "")
            elif "llm_answer" in event:
                full_response = event["llm_answer"].get("final_answer", "")
            elif "irrelevant" in event:
                full_response = event["irrelevant"].get("final_answer", "")

        # 显示最终答案
        if not full_response:
            full_response = "任务处理完成，结果已更新。"

        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})