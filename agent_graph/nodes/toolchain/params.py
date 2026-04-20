import json
import os
import re
import torch
from agent_graph.state import AgentState
from agent_graph.prompts.toolchain_prompts import build_parameter_generator_prompt
from configs import TOOL_LIST, TOOL_ARGS
from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history
from utils.user_context import get_or_create_run_dir, get_session_dir
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def _list_session_files(lang: str) -> str:
    """Return a formatted string listing all user-uploaded files in the session directory."""
    session_dir = get_session_dir()
    if not session_dir or not os.path.isdir(session_dir):
        return "None" if lang == "en_US" else "无"
    entries = []
    for entry in sorted(os.scandir(session_dir), key=lambda e: e.name):
        if entry.is_file():
            size_kb = entry.stat().st_size / 1024
            entries.append(f"  - {entry.name}  ({size_kb:.1f} KB)  →  {entry.path}")
    if not entries:
        return "None" if lang == "en_US" else "无"
    return "\n".join(entries)


def generate_tool_params_node(state: AgentState) -> AgentState:
    param_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    history_str = format_history(state.get("chat_history", []))
    rag_suggestion = state.get("rag_suggestion", {})
    tool_sequences = state.get("tool_sequence", [])
    is_workflow = state.get("is_workflow", False)
    selected_workflow = state.get("selected_workflow", "")
    pre_files = state.get("pre_files", [])

    print(f"\n[Param Generator] Configuring parameters for {len(tool_sequences)} step(s)...")
    if not tool_sequences:
        state["tool_calls"] = []
        return state

    user_feedback = state.get("user_feedback", "")
    old_tool_calls = state.get("tool_calls", [])
    final_tool_calls = []
    last_step_output_file = ""

    for i, tool_name in enumerate(tool_sequences):

        # ── workflow 模式：强制关键参数，跳过 LLM ──────────────────────────────
        if is_workflow and selected_workflow:
            run_dir = get_or_create_run_dir()

            # input 固定指向 run_dir 下的前置文件
            # 若文件不存在（重试时 run_dir 已重建），从 pre_files 内容重新写入
            input_path = ""
            if pre_files and run_dir:
                pf = pre_files[0]
                safe_name = os.path.basename(pf["filename"])
                dest = os.path.join(run_dir, safe_name)
                if not os.path.exists(dest):
                    with open(dest, "w", encoding="utf-8") as _f:
                        _f.write(pf["content"])
                    ui_print(f"[Param Generator] Re-wrote pre-file to new run_dir: {dest}")
                input_path = dest

            tool_call = {
                "tool_name": selected_workflow,
                "tool_args": {
                    "kwargs": {
                        "pipeline": selected_workflow,
                        "input":    input_path,
                        "outdir":   "results",   # command_builder 会拼到 run_dir 下
                    }
                }
            }
            ui_print(f"[Param Generator] Workflow parameter has been set mandatorily: pipeline={selected_workflow}, input={input_path}")
            final_tool_calls.append(tool_call)
            continue
        # ──────────────────────────────────────────────────────────────────────

        # ── 普通工具：RAG + LLM 生成参数 ──────────────────────────────────────
        tool_real_name = ""
        for t in TOOL_LIST:
            if t.lower() in tool_name.lower():
                tool_real_name = t.lower()
                break
        if not tool_real_name:
            print(f"  [Warning] Skipping unrecognized tool: {tool_name}")
            continue

        current_schema = str(TOOL_ARGS.get(tool_real_name, "{}"))
        current_rag = rag_suggestion.get(tool_real_name, "No relevant documentation found.")

        print(f"  > Configuring step {i + 1}: {tool_name} (base: {tool_real_name})")

        last_params_snapshot = ""
        for old_call in old_tool_calls:
            if tool_name.lower() == old_call.get("tool_name", "").lower():
                last_params_snapshot = json.dumps(
                    old_call.get("tool_args", {}), indent=2, ensure_ascii=False
                )
                break

        lang = get_lang()
        final_prompt = build_parameter_generator_prompt(lang).format(
            step_num=i + 1,
            tool_name=tool_name,
            schema=current_schema,
            rag=current_rag,
            session_files=_list_session_files(lang),
            user_input=user_input,
            history=history_str,
            last_params=last_params_snapshot,
            user_feedback=user_feedback if user_feedback else "N/A",
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
            kwargs = args.get("kwargs", {})
            last_step_output_file = (
                kwargs.get("output")
                or kwargs.get("output_file")
                or kwargs.get("output_dir")
                or kwargs.get("o")
                or ""
            )
        except Exception as e:
            print(f"  [Error] Failed to configure {tool_name}: {e}")
            continue

    state["tool_calls"] = final_tool_calls
    return state
