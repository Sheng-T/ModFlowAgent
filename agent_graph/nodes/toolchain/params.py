import json
import re
import torch
from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import (
    build_parameter_generator_prompt,
)
from configs import TOOL_LIST, TOOL_ARGS, WORKFLOW_PIPELINE_ARGS
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history

# 统一使用顶级 `utils.ui_logger` 导出
from utils.ui_logger import ui_print

def generate_tool_params_node(state: AgentState) -> AgentState:
    param_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    rag_suggestion = state.get("rag_suggestion", {})
    tool_sequences = state.get("tool_sequence", [])
    is_workflow = state.get("is_workflow", False)
    selected_workflow = state.get("selected_workflow")  # 例如 "methylong"

    print(f"\n[Param Generator] 正在为 {len(tool_sequences)} 个步骤配置参数...")
    if not tool_sequences:
        state["tool_calls"] = []
        return state

    user_feedback = state.get("user_feedback", "")
    old_tool_calls = state.get("tool_calls", [])
    final_tool_calls = []
    last_step_output_file = ""

    for i, tool_name in enumerate(tool_sequences):

        # ───────────────────── 取 schema 和 RAG ───────────────────────
        if is_workflow and selected_workflow:
            # workflow 模式：schema 来自 WORKFLOW_PIPELINE_ARGS，RAG key 是 pipeline 名
            tool_real_name = selected_workflow
            current_schema = str(WORKFLOW_PIPELINE_ARGS.get(selected_workflow, "{}"))
            current_rag = rag_suggestion.get(selected_workflow, "未找到相关 RAG 文档。")
        else:
            # 普通工具：schema 来自 TOOL_ARGS，RAG key 是工具名
            tool_real_name = ""
            for t in TOOL_LIST:
                if t.lower() in tool_name.lower():
                    tool_real_name = t.lower()
                    break
            if not tool_real_name:
                print(f"  [Warning] 跳过无法识别的工具: {tool_name}")
                continue
            current_schema = str(TOOL_ARGS.get(tool_real_name, "{}"))
            current_rag = rag_suggestion.get(tool_real_name, "未找到相关 RAG 文档。")
        # ─────────────────────────────────────────────────────────────

        print(f"  > 正在配置第 {i + 1} 步: {tool_name} (base: {tool_real_name})")

        last_params_snapshot = ""
        if old_tool_calls:
            for old_call in old_tool_calls:
                if tool_name.lower() == old_call.get("tool_name", "").lower():
                    last_params_snapshot = json.dumps(
                        old_call.get("tool_args", {}), indent=2, ensure_ascii=False
                    )
                    break

        final_prompt = build_parameter_generator_prompt().format(
            step_num=i + 1,
            tool_name=tool_name,
            schema=current_schema,
            rag=current_rag,
            user_input=user_input,
            history=history_str,
            last_params=last_params_snapshot,
            user_feedback=user_feedback if user_feedback else "无",
            last_output=last_step_output_file,
        )

        try:
            torch.cuda.empty_cache()
            raw_response = param_llm.invoke(final_prompt)
            content = raw_response if isinstance(raw_response, str) else raw_response.content
            clean_json_str = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            if "```json" in clean_json_str:
                clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()

            current_call = json.loads(clean_json_str)
            print(f"\n[Param Generator] {current_call}")
            final_tool_calls.append(current_call)

            args = current_call.get("tool_args", {})
            if args:
                kwargs = args.get("kwargs", {})
                last_step_output_file = (
                    kwargs.get("output")
                    or kwargs.get("output_file")
                    or kwargs.get("output_dir")
                    or kwargs.get("o")
                    or ""
                )
        except Exception as e:
            print(f"  [Error] {tool_name} 配置失败: {e}")
            continue

    state["tool_calls"] = final_tool_calls
    return state


