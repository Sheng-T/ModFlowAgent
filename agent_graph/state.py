from typing import TypedDict, Annotated, List, Dict

EMPTY_STATE = {
    "identified_tools": [],
    "tool_calls": [],
    "tool_output": "",
    "rag_suggestion": {},
    "tool_sequence": [],
    "user_approval": False,
    "user_feedback": "",
    "final_answer": "",
    "next_node": "",
    "selected_workflow": "",
    "is_workflow": False
    # 注意：这里不要放 chat_history，因为我们不想重置它
}


# 定义 Agent 的核心状态
class AgentState(TypedDict):
    """
    Agent 的核心状态，用于在图的不同节点之间传递信息。
    """
    # 用户的原始输入，用于 LLM 决策
    input: str

    identified_tools: List[str]

    # 存储工具调用列表 (由 LLM 规划)
    tool_calls: List[str]

    # 存储工具执行后的结果或错误信息
    tool_output: List[str]

    # RAG 检索到的工具使用建议或背景知识
    rag_suggestion: dict

    tool_sequence: List[str]

    user_feedback: str  # 用户的修改建议

    # 最终反馈给用户的答案
    final_answer: str

    chat_history: List[Dict[str, str]]  # 存储对话历史：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

    next_node: str

    is_workflow: bool # 判断工具还是工作流

    selected_workflow: str # workflow select
