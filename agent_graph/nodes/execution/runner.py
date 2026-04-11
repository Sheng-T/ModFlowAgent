import os
import shutil

from agent_graph.state import AgentState
from configs import TOOL_LIST
from runtime.env_wrapper import EnvWrapper
from runtime.executor import ToolExecutor
from utils.nodes_utils import build_command_for_call
from utils.user_context import get_run_dir, get_session_dir

from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def _collect_run_outputs(run_dir: str) -> list[str]:
    """返回 run_dir 下所有文件的绝对路径。"""
    if not run_dir or not os.path.isdir(run_dir):
        return []
    return [
        os.path.join(run_dir, name)
        for name in os.listdir(run_dir)
        if os.path.isfile(os.path.join(run_dir, name))
    ]


def _move_outputs_to_session(run_dir: str, session_dir: str):
    """将 run_dir 下所有文件移动到 session_dir，然后删除 run_dir。"""
    for fpath in _collect_run_outputs(run_dir):
        dest = os.path.join(session_dir, os.path.basename(fpath))
        # 同名文件加时间戳后缀，避免覆盖
        if os.path.exists(dest):
            base, ext = os.path.splitext(os.path.basename(fpath))
            import time
            dest = os.path.join(session_dir, f"{base}_{int(time.time())}{ext}")
        shutil.move(fpath, dest)
        ui_print(f"[Executor] 输出文件已归档: {os.path.basename(dest)}")
    shutil.rmtree(run_dir, ignore_errors=True)
    ui_print(f"[Executor] 运行目录已清理")


def _cleanup_run_dir(run_dir: str):
    """执行失败时删除整个 run_dir（含不完整的输出文件）。"""
    if run_dir and os.path.isdir(run_dir):
        shutil.rmtree(run_dir, ignore_errors=True)
        ui_print(f"[Executor] 执行失败，运行目录已清理")


def _write_pre_files(pre_files: list, session_dir: str):
    """将前置文件写入 session_dir，并返回实际写入路径列表。"""
    written = []
    for pf in pre_files:
        dest = os.path.join(session_dir, pf["filename"])
        with open(dest, "w", encoding="utf-8") as f:
            f.write(pf["content"])
        ui_print(f"[Executor] 已写入前置文件: {pf['filename']}")
        written.append(dest)
    return written


def execute_commands_node(state: AgentState) -> dict:
    wrapper = EnvWrapper()
    executor = ToolExecutor()
    lang = get_lang()

    tool_calls = state.get("tool_calls", [])
    history = state.get("chat_history", [])
    next_node = "summarizer"
    tool_output = []

    is_workflow = state.get("is_workflow", False)
    pending_commands = state.get("pending_commands", [])

    def _msg(en: str, zh: str) -> str:
        return en if lang == "en_US" else zh

    if is_workflow:
        for raw_cmd in pending_commands:
            if "error" in raw_cmd.lower():
                history.append({"role": "assistant", "content": _msg(
                    f"Pre-validation intercepted an error: {raw_cmd}",
                    f"系统拦截预校验失败: {raw_cmd}",
                )})
                next_node = "param_generator"
                break

            ui_print(f"\n[Executor] Running: {raw_cmd}")
            final_cmd = wrapper.wrap_command("workflow", raw_cmd, is_workflow=True)
            resp = executor.run(final_cmd)

            if resp["status"] == "success":
                output = resp.get("output", "")
                tool_output.append(output)
                history.append({"role": "assistant", "content": _msg(
                    f"Command succeeded.\nOutput: {output[-200:]}",
                    f"命令执行成功\n输出: {output[-200:]}",
                )})
            else:
                next_node = "param_generator"
                error_log = resp["stderr"][:1500] + "\n...\n" + resp["stderr"][-500:]
                ui_print(f"\n[Executor] Failed: {error_log}")
                history.append({"role": "assistant", "content": _msg(
                    f"Execution failed:\n{error_log}\nI will correct the parameters.",
                    f"执行失败，报错如下：\n{error_log}\n我需要根据这个错误修正参数。",
                )})
                _cleanup_run_dir(get_run_dir())
                break
    else:
        pre_files = state.get("pre_files", [])
        if pre_files:
            session_dir = get_session_dir()
            if session_dir:
                _write_pre_files(pre_files, session_dir)
            else:
                ui_print("[Executor] Warning: session_dir unavailable, pre-files not written")

        for i, call in enumerate(tool_calls):
            tool_name = call["tool_name"]
            tool_name_array = tool_name.split("_")
            base_name = tool_name_array[0]
            has_subcommand = len(tool_name_array) > 1

            if base_name not in TOOL_LIST:
                history.append({"role": "assistant", "content": _msg(
                    f"Tool '{base_name}' is not registered in the system. Please re-select.",
                    f"工具：{base_name}不在系统中，请重新规划选择。",
                )})
                return {"chat_history": history, "next_node": "tools_selector"}

            raw_cmd = pending_commands[i] if i < len(pending_commands) else build_command_for_call(call, is_workflow=False)

            if "error" in raw_cmd.lower():
                history.append({"role": "assistant", "content": _msg(
                    f"Pre-validation failed for {tool_name}: {raw_cmd}. Please reconfigure.",
                    f"系统拦截：{tool_name} 预校验失败: {raw_cmd}，请重新配置参数。",
                )})
                break

            ui_print(f"\n[Executor] Running: {raw_cmd}")
            final_cmd = wrapper.wrap_command(base_name, raw_cmd, is_workflow=False)
            resp = executor.run(final_cmd)

            if resp["status"] == "success":
                output = resp.get("output", "")
                tool_output.append(output)
                history.append({"role": "assistant", "content": _msg(
                    f"{tool_name} succeeded.\nOutput summary: {output[-200:]}",
                    f"{tool_name} 成功\n输出摘要: {output[-200:]}",
                )})
            else:
                next_node = "param_generator" if has_subcommand else "summarizer"
                error_log = resp["stderr"][:1500] + "\n...\n" + resp["stderr"][-500:]
                ui_print(f"\n[Executor] Failed: {error_log}")
                history.append({"role": "assistant", "content": _msg(
                    f"Execution of {tool_name} failed:\n{error_log}\nI will correct the parameters.",
                    f"我尝试执行了 {tool_name}，但失败了。报错如下：\n{error_log}\n我需要根据这个错误修正参数。",
                )})
                _cleanup_run_dir(get_run_dir())
                break
            _cleanup_run_dir(get_run_dir())
            break

    # 成功路径不在此处移动文件：summarize 节点完成分析后统一移动并清理 run_dir

    return {"chat_history": history, "next_node": next_node, "tool_output": tool_output}

