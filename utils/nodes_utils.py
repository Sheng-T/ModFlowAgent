from typing import List, Dict

from configs import DATA_PATH
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY, WORKFLOW_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from tools.workflow.command_builder import build_workflow_command
from utils.user_context import get_session_dir, get_or_create_run_dir


def format_history(history: List[Dict[str, str]]) -> str:
    """将历史字典转化为 LLM 易读的文本"""
    if not history:
        return "无"
    return "\n".join([f"[{msg['role']}]: {msg['content']}" for msg in history])

# utils/nodes_utils.py
def build_command_for_call(call: dict, is_workflow: bool = False) -> str:
    tool_name = call["tool_name"]
    tool_args = call["tool_args"]
    tool_name_array = tool_name.split("_")
    base_name = tool_name_array[0]
    has_subcommand = len(tool_name_array) > 1  # ← 关键判断

    sub_cmd_str = " ".join(tool_name_array[1:]) if has_subcommand else ""
    last_sub_command = tool_name_array[-1] if has_subcommand else ""

    session_dir = get_session_dir()
    run_dir = get_or_create_run_dir() if session_dir else None

    if is_workflow:
        # workflow: input 从 run_dir 取（前置文件写在那里），outdir 也在 run_dir 下
        wf_data_path = dict(DATA_PATH.get("workflow", DATA_PATH.get("nextflow", {})))
        if session_dir:
            wf_data_path["base_data_dir"] = session_dir
        if run_dir:
            wf_data_path["out_dir"] = run_dir   # --outdir → run_dir/results
            wf_data_path["work_dir"] = run_dir
        verify_func = WORKFLOW_REGISTRY.get(tool_name)
        if verify_func:
            return verify_func(tool_args, wf_data_path)
        return build_workflow_command(tool_args.get("kwargs", tool_args), wf_data_path)

    # 普通工具：输入从 session_dir 查找，输出写入 run_dir
    tool_data_path = dict(DATA_PATH.get(base_name, {}))
    if session_dir:
        tool_data_path["base_data_dir"] = session_dir
    if run_dir:
        tool_data_path["out_dir"] = run_dir

    verify_func = TOOL_REGISTRY.get(base_name)
    if verify_func:
        return verify_func(last_sub_command, sub_cmd_str, tool_args, tool_data_path)

    # 兜底：无子命令时直接拼 base_name + kwargs
    arg_str = build_shell_args(tool_args)
    if has_subcommand:
        return f"{base_name} {sub_cmd_str} {arg_str}".strip()
    else:
        return f"{base_name} {arg_str}".strip()
