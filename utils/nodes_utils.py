from typing import List, Dict

from configs import DATA_PATH
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY, WORKFLOW_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from tools.workflow.command_builder import build_workflow_command


def format_history(history: List[Dict[str, str]]) -> str:
    """将历史字典转化为 LLM 易读的文本"""
    if not history:
        return "无"
    return "\n".join([f"[{msg['role']}]: {msg['content']}" for msg in history])

def build_command_for_call(call: dict, is_workflow: bool = False) -> str:
    tool_name = call["tool_name"]
    tool_args = call["tool_args"]
    tool_name_array = tool_name.split("_")
    base_name = tool_name_array[0]
    sub_cmd_str = " ".join(tool_name_array[1:])
    last_sub_command = tool_name_array[-1]

    if is_workflow:
        # tool_name 就是 pipeline 名，如 "methylong"
        verify_func = WORKFLOW_REGISTRY.get(tool_name)
        if verify_func:
            return verify_func(tool_args, DATA_PATH.get("workflow", {}))
        else:
            return build_workflow_command(tool_name, tool_args)
    else:
        verify_func = TOOL_REGISTRY.get(base_name)
        if verify_func:
            return verify_func(last_sub_command, sub_cmd_str, tool_args, DATA_PATH[base_name])
        else:
            return f"{base_name} {sub_cmd_str} {build_shell_args(tool_args)}".strip()


