from typing import TypedDict, List, Dict

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
    "is_workflow": False,
    "user_choice": None,
    "pending_commands": [],
    "pre_files": [],
    "run_dir": "",
    "analysis_images": [],
}


# 定义 Agent 的核心状态
class AgentState(TypedDict):
    """
    Agent 的核心状态，用于在图的不同节点之间传递信息。
    """
    # 用户的原始输入，用于 LLM 决策
    input: str

    # 用户的路由选择：可选值为 "answer"（生物问答）或 "tools"（工具调用），或 None（自动判断）
    user_choice: str | None

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

    is_workflow: bool  # 判断工具还是工作流

    selected_workflow: str  # workflow select

    pending_commands: List[str]

    # workflow 前置文件（如 samplesheet.csv），执行前写入 session_dir
    pre_files: List[Dict]

    # 本次运行的临时目录（由 review 节点写入，summarizer 读取后移文件并清理）
    run_dir: str

    # 分析产生的图表文件路径列表（已移到 session_dir 下）
    analysis_images: List[str]
