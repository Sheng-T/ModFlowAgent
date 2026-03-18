from langgraph.graph import StateGraph, END
from agent_graph.nodes import intent_router, rag_retrieval, tool_planner, execute_tool, output_summarizer, \
    non_relevant_response, router_selector, general_llm_answer, validator_node, tools_selector, parameter_generator, \
    human_review_node, end_node
from agent_graph.state import AgentState
from IPython.display import Image, display


def save_graph_image(app_instance, filename="bioagent_graph.txt"):
    """
    直接保存 Mermaid 源码到本地，无需联网渲染
    """
    try:
        # 获取纯文本格式的逻辑源码
        mermaid_code = app_instance.get_graph().draw_mermaid()

        # 保存为本地文本文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        print(f"\n[System] 流程图已保存至本地: {filename}")
        print(f"提示：该文件包含图的所有逻辑定义，可用任何文本编辑器查看。")
    except Exception as e:
        print(f"\n[System] 保存失败: {e}")

def create_agent_graph(agent_name: str, is_save_graph_image: bool = False, graph_image_filename: str="") -> StateGraph:
    # 1. 实例化图
    workflow = StateGraph(AgentState)

    # 2. 添加所有节点 (Nodes)
    workflow.add_node("router", intent_router)
    workflow.add_node("tools_selector", tools_selector)
    workflow.add_node("rag", rag_retrieval)
    workflow.add_node("planner", tool_planner)
    workflow.add_node("param_generator", parameter_generator)
    workflow.add_node("validator", validator_node)
    workflow.add_node("human_reviewer", human_review_node)
    workflow.add_node("executor", execute_tool)
    workflow.add_node("summarizer", output_summarizer)
    workflow.add_node("llm_answer", general_llm_answer)
    workflow.add_node("irrelevant", non_relevant_response)
    workflow.add_node("end_node", end_node)

    # 3. 设置入口点 (Entry Point)
    workflow.set_entry_point("router")

    # 4. 定义路由/边 (Edges)

    # A. 路由器的条件路由
    workflow.add_conditional_edges(
        "router",
        # 路由函数就是 router 节点本身，它返回下一个节点名称
        lambda state: router_selector(state),
        {
            "route_to_tools": "tools_selector",
            "route_to_answer": "llm_answer",
            "route_to_irrelevant": "irrelevant",
        }
    )

    # B. 核心流水线：选择工具 -> RAG检索 -> 规划顺序 -> 填充参数 -> 校验 -> 执行
    workflow.add_edge("tools_selector", "rag")
    workflow.add_edge("rag", "planner")

    # C. Planner 的条件路由 (检查是否需要调用工具)
    workflow.add_conditional_edges(
        "planner",
        lambda state: "generate_parameters" if state.get("tool_sequence") else "route_to_summarize",
        {
            "generate_parameters": "param_generator",  # 规划了顺序，去填参数
            "route_to_summarize": "summarizer",
        }
    )

    # D. Executor 和 Summarizer 的最终流转
    workflow.add_edge("param_generator", "validator")
    workflow.add_edge("validator", "human_reviewer")  # 校验通过 -> 执行

    workflow.add_conditional_edges(
        "human_reviewer",
        lambda state: state.get("next_node", "param_generator"),  # 默认回退到参数生成
        {
            "tools_selector": "tools_selector",
            "executor": "executor",
            "rag": "rag",
            "param_generator": "param_generator",
            "end_node": "end_node"
        }
    )

    workflow.add_conditional_edges(
        "executor",
        lambda state: state.get("next_node", "param_generator"),  # 默认回退到参数生成
        {
            "param_generator": "param_generator",
            "summarizer": "summarizer",
            "tools_selector": "tools_selector",
        }
    )
    workflow.add_edge("llm_answer", END)
    workflow.add_edge("summarizer", END)      # 总结完，流程结束
    workflow.add_edge("irrelevant", END)      # 不相关回复，流程结束
    workflow.add_edge("end_node", END)      # 流程结束

    # 5. 编译图
    app = workflow.compile()
    app.name = agent_name
    if is_save_graph_image:
        save_graph_image(app, graph_image_filename)
    return app