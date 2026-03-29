from agent_graph.state import AgentState
from configs import TOOL_LIST, DATA_PATH
from runtime.env_wrapper import EnvWrapper
from runtime.executor import ToolExecutor
from tools.registry import TOOL_REGISTRY, COMMAND_REGISTRY
from tools.toolchain.command_builder import build_shell_args
from utils.nodes_utils import build_command_for_call

# 多层级导入保证兼容性
try:
    from utils.ui_logger import ui_print
except ImportError:
    try:
        from ....utils.ui_logger import ui_print
    except ImportError:
        ui_print = print


def execute_commands_node(state: AgentState) -> dict:
    wrapper = EnvWrapper()
    executor = ToolExecutor()

    tool_calls = state.get("tool_calls", [])
    history = state.get("chat_history", [])
    next_node = "summarizer"
    tool_output = []

    for call in tool_calls:
        tool_name = call["tool_name"]
        # args = call["tool_args"]

        tool_name_array = tool_name.split("_")
        base_name = tool_name_array[0]
        has_subcommand = len(tool_name_array) > 1

        if base_name not in TOOL_LIST:
            history.append({"role": "assistant", "content": f"工具：{base_name}不在系统中，请重新规划选择。"})
            return {"chat_history": history, "next_node": "tools_selector"}

        # raw_cmd = build_command_for_call(call)
        raw_cmd = build_command_for_call(call, is_workflow=state.get("is_workflow", False))

        if "error" in raw_cmd.lower():
            error_msg = f"工具 {tool_name} 预校验失败: {raw_cmd}"
            history.append({"role": "assistant", "content": f"系统拦截：{error_msg}，请重新配置参数。"})
            break

        ui_print(f"\n[Executor] 正在执行: {raw_cmd}")
        final_cmd = wrapper.wrap_command(base_name, raw_cmd)
        ui_print(f"\n[Executor] 真实执行: {final_cmd}")
        resp = executor.run(final_cmd)

        if resp["status"] == "success":
            output = resp.get("output", "")
            success_log = output[-200:]
            success_msg = f"{tool_name} 成功\n输出摘要: {success_log}"
            ui_print(f"\n[Executor] {success_msg}")
            tool_output.append(output)
            history.append({"role": "assistant", "content": f"{success_msg} 输出路径已记录。"})
        else:
            # next_node = "nfcore_param_generator" if base_name == "workflow" else "param_generator"
            next_node = "param_generator" if has_subcommand else "summarizer"
            error_log = resp["stderr"][:1500] + "\n...\n" + resp["stderr"][-500:]
            fail_msg = f"{tool_name} 执行失败！报错信息:\n{error_log}"
            ui_print(f"\n[Executor] 执行失败: {fail_msg}")
            history.append(
                {
                    "role": "assistant",
                    "content": f"我尝试执行了 {tool_name}，但失败了。报错如下：\n{error_log}\n我需要根据这个错误修正参数。",
                }
            )
            break

    return {"chat_history": history, "next_node": next_node, "tool_output": tool_output}

