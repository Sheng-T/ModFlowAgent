
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import (
    build_tools_selector_prompt,
)
from configs import TOOL_DESCIPTION, TOOLS_DOC

from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history

# 多层级导入保证兼容性
try:
    from utils.ui_logger import ui_print
except ImportError:
    try:
        from ....utils.ui_logger import ui_print
    except ImportError:
        ui_print = print

def select_tools_node(state: AgentState) -> AgentState:
    user_input = state["input"]
    user_feedback = state.get("user_feedback", "")
    history_str = format_history(state.get("chat_history", []))
    tool_sequence = state.get("tool_sequence", [])
    ui_print(f"\n[Tools Selector] 正在分析任务涉及的工具...")
    tools_info = "\n".join([f"- {t['name']}: {t['description']}" for t in TOOL_DESCIPTION])
    prompt = ChatPromptTemplate.from_template(build_tools_selector_prompt())
    selector_llm = get_llm_instance(is_planner=True)
    chain = prompt | selector_llm | JsonOutputParser()
    try:
        response = chain.invoke(
            {
                "input": user_input,
                "tools_info": tools_info,
                "history": history_str,
                "tool_sequence": tool_sequence,
                "user_feedback": user_feedback,
            }
        )
        selected = response.get("selected_tools", [])
        valid_tools = [t for t in selected if t in TOOLS_DOC.keys()]

        # 兜底关键词匹配（不变）
        if not valid_tools:
            if "basecall" in user_input.lower() or "dorado" in user_input.lower():
                valid_tools.append("dorado")
            if "sort" in user_input.lower() or "index" in user_input.lower():
                valid_tools.append("samtools")
            if any(k in user_input.lower() for k in ["nextflow", "nf-core", "workflow", "pipeline", "workflow"]):
                valid_tools.append("workflow")

        # 去重保序
        ordered = list(dict.fromkeys(valid_tools))

        state["identified_tools"] = ordered[:1]  # 单工具：取第一个

        state["is_workflow"] = (
            len(state["identified_tools"]) > 0
            and state["identified_tools"][0] == "workflow"
        )

        ui_print(f"[Tools Selector] 已确定工具: {state['identified_tools']}")
        ui_print(f"[Tools Selector] 是否为 workflow 工具: {state['is_workflow']}")
        ui_print(f"[Tools Selector] 理由: {response.get('reason', '无')}")

    except Exception as e:
        ui_print(f"[Tools Selector Error] 解析失败，使用默认兜底: {e}")
        state["identified_tools"] = []
        state["is_workflow"] = False

    return state


