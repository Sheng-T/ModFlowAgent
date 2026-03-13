from typing import TypedDict, Annotated, List

EMPTY_STATE = {
    "identified_tools": [],
    "tool_calls": [],
    "tool_output": "",
    "rag_suggestion": "",
    "tool_sequence": [],
    "user_approval": False,
    "user_feedback": "",
    "final_answer": ""
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
    tool_output: str

    # RAG 检索到的工具使用建议或背景知识
    rag_suggestion: str

    tool_sequence: List[str]

    tool_args_schema: List[str]

    user_approval: bool  # 用户是否批准执行

    user_feedback: str  # 用户的修改建议

    # 最终反馈给用户的答案
    final_answer: str