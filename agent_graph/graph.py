from langgraph.graph import END, StateGraph
from agent_graph.nodes import (
    answer_general_question_node,
    classify_intent_route,
    confirm_nfcore_workflow_node,
    execute_commands_node,
    finish_session_node,
    generate_nfcore_params_node,
    generate_tool_params_node,
    handle_irrelevant_request_node,
    plan_tool_steps_node,
    reset_session_state_node,
    retrieve_nfcore_docs_node,
    retrieve_tool_docs_node,
    review_execution_plan_node,
    select_nfcore_pipeline_node,
    select_tools_node,
    summarize_execution_result_node,
    validate_nfcore_params_node,
    validate_tool_calls_node,
)
from agent_graph.state import AgentState


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
    workflow.add_node("router", reset_session_state_node)
    workflow.add_node("tools_selector", select_tools_node)
    workflow.add_node("rag", retrieve_tool_docs_node)
    workflow.add_node("nfcore_selector", select_nfcore_pipeline_node)
    workflow.add_node("nfcore_workflow_confirm", confirm_nfcore_workflow_node)
    workflow.add_node("nfcore_rag", retrieve_nfcore_docs_node)
    workflow.add_node("nfcore_param_generator", generate_nfcore_params_node)
    workflow.add_node("nfcore_validator", validate_nfcore_params_node)
    workflow.add_node("planner", plan_tool_steps_node)
    workflow.add_node("param_generator", generate_tool_params_node)
    workflow.add_node("validator", validate_tool_calls_node)
    workflow.add_node("human_reviewer", review_execution_plan_node)
    workflow.add_node("executor", execute_commands_node)
    workflow.add_node("summarizer", summarize_execution_result_node)
    workflow.add_node("llm_answer", answer_general_question_node)
    workflow.add_node("irrelevant", handle_irrelevant_request_node)
    workflow.add_node("end_node", finish_session_node)

    # 3. 设置入口点 (Entry Point)
    workflow.set_entry_point("router")

    # 4. 定义路由/边 (Edges)

    # A. 路由器的条件路由
    workflow.add_conditional_edges(
        "router",
        # 路由函数就是 router 节点本身，它返回下一个节点名称
        lambda state: classify_intent_route(state),
        {
            "route_to_tools": "tools_selector",
            "route_to_workflow": "nfcore_selector",
            "route_to_answer": "llm_answer",
            "route_to_irrelevant": "irrelevant",
        }
    )

    # B. 核心流水线：根据工具分支进入通用链路或 nf-core 链路
    workflow.add_conditional_edges(
        "tools_selector",
        lambda state: "nfcore_branch"
        if "nextflow" in state.get("identified_tools", [])
        else "default_branch",
        {
            "default_branch": "rag",
            "nfcore_branch": "nfcore_selector",
        },
    )
    workflow.add_edge("nfcore_selector", "nfcore_workflow_confirm")
    workflow.add_conditional_edges(
        "nfcore_workflow_confirm",
        lambda state: state.get("next_node", "nfcore_rag"),
        {
            "nfcore_selector": "nfcore_selector",
            "nfcore_rag": "nfcore_rag",
        },
    )
    workflow.add_edge("nfcore_rag", "nfcore_param_generator")
    workflow.add_edge("nfcore_param_generator", "nfcore_validator")
    workflow.add_edge("nfcore_validator", "human_reviewer")
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
            "nfcore_rag": "nfcore_rag",
            "nfcore_param_generator": "nfcore_param_generator",
            "end_node": "end_node"
        }
    )

    workflow.add_conditional_edges(
        "executor",
        lambda state: state.get("next_node", "param_generator"),  # 默认回退到参数生成
        {
            "param_generator": "param_generator",
            "nfcore_param_generator": "nfcore_param_generator",
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