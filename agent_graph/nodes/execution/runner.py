import os
import shutil
import re

from agent_graph.state import AgentState
from tools.analyzers.registry import extract_output_paths
from configs import TOOL_LIST
from runtime.env_wrapper import EnvWrapper, cleanup_temp_scripts
from runtime.executor import ToolExecutor
from utils.nodes_utils import build_command_for_call
from utils.user_context import get_run_dir, get_session_dir

from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def _make_review_command(raw_cmd: str, run_dir: str = "") -> str:
    cmd = (raw_cmd or "").strip()
    if not cmd:
        return cmd
    if run_dir:
        cmd = cmd.replace(run_dir, "{run_dir}")
    if "|| (" in cmd and cmd.startswith("[ -f "):
        cmd = cmd.split("|| (", 1)[1].strip()
        if cmd.endswith(")"):
            cmd = cmd[:-1].rstrip()
    cmd = re.sub(r'^\s*:\s+"[^"]+"\s*;\s*', "", cmd).strip()
    cmd = re.sub(r'\s*&&\s*touch\s+"[^"]+"\s*$', "", cmd).strip()
    return cmd




def _format_error(resp: dict, tail: int = 3000) -> str:
    """取 stdout + stderr 各自末尾拼成可读错误信息，优先展示末尾（关键错误通常在最后）。"""
    stdout = (resp.get("stdout") or "").strip()
    stderr = (resp.get("stderr") or "").strip()
    parts = []
    if stderr:
        parts.append("--- stderr ---\n" + (stderr[-tail:] if len(stderr) > tail else stderr))
    if stdout:
        parts.append("--- stdout ---\n" + (stdout[-tail:] if len(stdout) > tail else stdout))
    return "\n".join(parts) if parts else "(no output)"


def _cleanup_run_dir(run_dir: str):
    if not run_dir or not os.path.isdir(run_dir):
        return
    nf_subdirs = {"work", "results", ".nextflow"}
    for entry in os.scandir(run_dir):
        if entry.name in nf_subdirs or (entry.name.startswith(".nextflow")):
            if entry.is_dir():
                shutil.rmtree(entry.path, ignore_errors=True)
            else:
                try:
                    os.unlink(entry.path)
                except OSError:
                    pass
    ui_print(f"[Executor] Execution failed, intermediate files cleaned up (pre-files preserved)")


def _write_pre_files(pre_files: list, session_dir: str):
    """将前置文件写入 session_dir，并返回实际写入路径列表。"""
    written = []
    for pf in pre_files:
        dest = os.path.join(session_dir, pf["filename"])
        with open(dest, "w", encoding="utf-8") as f:
            f.write(pf["content"])
        ui_print(f"[Executor] Pre-file written: {pf['filename']}")
        written.append(dest)
    return written


def _collect_result_artifacts(commands: list[str], run_dir: str = "") -> list[str]:
    artifacts: list[str] = []
    for path in extract_output_paths(commands):
        if os.path.isfile(path):
            artifacts.append(path)
            continue
        if os.path.isdir(path):
            try:
                for entry in sorted(os.scandir(path), key=lambda e: e.name):
                    if entry.is_file():
                        artifacts.append(entry.path)
            except OSError:
                continue
    if run_dir and os.path.isdir(run_dir):
        for entry in sorted(os.scandir(run_dir), key=lambda e: e.name):
            if entry.is_file() and entry.name.endswith((".html", ".zip", ".txt", ".tsv", ".csv")):
                artifacts.append(entry.path)
    return list(dict.fromkeys(artifacts))


def execute_commands_node(state: AgentState) -> dict:
    wrapper = EnvWrapper()
    executor = ToolExecutor()
    lang = get_lang()

    tool_calls = state.get("tool_calls", [])
    history = state.get("chat_history", [])
    next_node = "summarizer"
    tool_output = []
    result_artifacts: list[str] = []

    workflow_type = state.get("workflow_type", "")
    is_local_workflow = workflow_type == "local"
    is_workflow = workflow_type == "nfcore"
    pending_commands = state.get("pending_commands", [])

    def _msg(en: str, zh: str) -> str:
        return en if lang == "en_US" else zh

    if is_local_workflow:

        import json as _json
        import sys as _sys
        import subprocess as _sp
        from utils.run_tracker import write_status as _write_status

        run_dir = state.get("run_dir") or get_session_dir() or ""
        if run_dir:
            os.makedirs(run_dir, exist_ok=True)

        ui_print("[PROGRESS_INIT] total=" + str(len(tool_calls))
                 + " steps=" + ",".join(c["tool_name"] for c in tool_calls))

        job_steps: list[dict] = []
        validation_failed = False

        for i, call in enumerate(tool_calls):
            tool_name = call["tool_name"]
            base_name = call.get("_base_tool") or tool_name.split("_")[0]
            runtime_override = call.get("_runtime_override") or None

            step_dir = os.path.join(run_dir, f"step{i + 1:02d}_{tool_name}") if run_dir else run_dir
            if step_dir:
                os.makedirs(step_dir, exist_ok=True)

            raw_cmd = (
                pending_commands[i]
                if i < len(pending_commands)
                else build_command_for_call(call, is_workflow=False)
            )

            if "error" in raw_cmd.lower():
                history.append({"role": "assistant", "content": _msg(
                    f"Pre-validation failed for step {i+1} ({tool_name}): {raw_cmd}",
                    f"步骤 {i+1} ({tool_name}) 预校验失败: {raw_cmd}",
                )})
                next_node = "param_generator"
                validation_failed = True
                break

            # Wrap the command (Singularity / conda / plain) for this step
            final_cmd = wrapper.wrap_command(
                base_name,
                raw_cmd,
                is_workflow=False,
                cwd=step_dir or run_dir,
                runtime_override=runtime_override,
            )

            # Write a durable shell script inside step_dir so the worker can run
            # it independently of any temp files created by wrap_command.
            cmd_script = os.path.join(step_dir, "_run.sh")
            with open(cmd_script, "w", encoding="utf-8") as _sf:
                _sf.write("#!/bin/bash\n")
                _sf.write(final_cmd + "\n")
            os.chmod(cmd_script, 0o755)

            job_steps.append({
                "tool_name":  tool_name,
                "raw_cmd":    raw_cmd,
                "review_cmd": _make_review_command(raw_cmd, run_dir),
                "cmd_script": cmd_script,
                "step_dir":   step_dir,
            })

        if not validation_failed:
            session_dir   = get_session_dir() or ""
            workflow_name = (state.get("selected_workflow")
                             or (tool_calls[0].get("tool_name", "workflow") if tool_calls else "workflow"))

            # Write job descriptor
            job_data = {
                "run_dir":       run_dir,
                "session_dir":   session_dir,
                "workflow_name": workflow_name,
                "workflow_type": "local",
                "lang":          lang,
                "prereq_params": state.get("local_prereq_params", {}),
                "steps":         job_steps,
            }
            job_path = os.path.join(run_dir, "job.json")
            with open(job_path, "w", encoding="utf-8") as _jf:
                _json.dump(job_data, _jf, ensure_ascii=False)

            run_meta = {
                "version":            1,
                "workflow":           workflow_name,
                "modcaller":          state.get("local_prereq_params", {}).get("modcaller", ""),
                "caller":             state.get("local_prereq_params", {}).get("caller", ""),
                "modification_type":  state.get("local_prereq_params", {}).get("modification_type", ""),
                "data_file":          state.get("local_prereq_params", {}).get("data_file", ""),
                "reference":          state.get("local_prereq_params", {}).get("reference", ""),
                "device":             state.get("local_prereq_params", {}).get("device", ""),
                "caller_profile_version": state.get("local_prereq_params", {}).get("_caller_profile_version", 1),
                "resolved_step_sequence": [step["tool_name"] for step in job_steps],
            }
            meta_path = os.path.join(run_dir, "run_meta.json")
            with open(meta_path, "w", encoding="utf-8") as _mf:
                _json.dump(run_meta, _mf, ensure_ascii=False, indent=2)

            # Write initial pending status (worker will overwrite to "running" immediately)
            _write_status(run_dir, {
                "status":             "pending",
                "pid":                None,
                "workflow_name":      workflow_name,
                "question":           state.get("input", ""),
                "started_at":         None,
                "finished_at":        None,
                "current_step":       None,
                "current_step_index": 0,
                "total_steps":        len(job_steps),
                "zip_path":           None,
                "analysis_images":    [],
                "text_summary":       "",
                "warnings":           [],
                "error":              None,
            })

            # Spawn detached worker — survives Streamlit session death
            # runner.py: agent_graph/nodes/execution/ → ../../.. → 项目根
            _proj_root     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            _worker_script = os.path.join(_proj_root, "worker", "pipeline_worker.py")
            with (open(os.path.join(run_dir, "worker_stdout.log"), "w") as _stdout_log,
                  open(os.path.join(run_dir, "worker_stderr.log"), "w") as _stderr_log):
                _sp.Popen(
                    [_sys.executable, _worker_script, run_dir],
                    start_new_session=True,
                    stdin=_sp.DEVNULL,
                    stdout=_stdout_log,
                    stderr=_stderr_log,
                )
                # Popen duplicates the fds; closing Python handles here is safe
            ui_print(f"[Executor] Detached worker spawned → run_dir={run_dir}")
            # Emit a special marker so the UI poller can start watching this run_dir
            ui_print(f"[WORKER_STARTED] run_dir={run_dir}")

            history.append({"role": "assistant", "content": _msg(
                f"Pipeline submitted in background ({len(job_steps)} steps). "
                "You can close the browser — results will be saved automatically when complete.",
                f"流水线已在后台提交（共 {len(job_steps)} 步）。"
                "可以关闭浏览器，运行完成后结果将自动保存。",
            )})

    elif is_workflow:
        import datetime as _dt
        from utils.run_tracker import write_status as _write_status

        _nf_run_dir  = state.get("run_dir") or ""
        _nf_workflow = (state.get("selected_workflow")
                        or (tool_calls[0].get("tool_name", "workflow") if tool_calls else "workflow"))
        _nf_started  = _dt.datetime.now(_dt.timezone.utc).isoformat()

        if _nf_run_dir:
            _write_status(_nf_run_dir, {
                "status":        "running",
                "pid":           os.getpid(),
                "workflow_name": _nf_workflow,
                "question":      state.get("input", ""),
                "started_at":    _nf_started,
                "finished_at":   None,
                "error":         None,
            })

        _nf_failed = False
        _nf_error  = None

        for raw_cmd in pending_commands:
            if "error" in raw_cmd.lower():
                history.append({"role": "assistant", "content": _msg(
                    f"Pre-validation intercepted an error: {raw_cmd}",
                    f"系统拦截预校验失败: {raw_cmd}",
                )})
                next_node = "param_generator"
                _nf_failed = True
                _nf_error  = raw_cmd
                break

            ui_print(f"\n[Executor] Running: {raw_cmd}")
            run_dir = _nf_run_dir or ""
            final_cmd = wrapper.wrap_command("workflow", raw_cmd, is_workflow=True,
                                             cwd=run_dir)
            resp = executor.run(final_cmd)

            if resp["status"] == "success":
                output = resp.get("output", "")
                tool_output.append(output)
                result_artifacts = _collect_result_artifacts([raw_cmd], run_dir)
                history.append({"role": "assistant", "content": _msg(
                    f"Command succeeded.\nOutput: {output[-200:]}",
                    f"命令执行成功\n输出: {output[-200:]}",
                )})
            else:
                next_node = "param_generator"
                error_log = _format_error(resp)
                _nf_failed = True
                _nf_error  = error_log
                ui_print(f"\n[Executor] Failed:\n{error_log}")
                history.append({"role": "assistant", "content": _msg(
                    f"Execution failed:\n{error_log}\nI will correct the parameters.",
                    f"执行失败，报错如下：\n{error_log}\n我需要根据这个错误修正参数。",
                )})
                break

        if _nf_run_dir:
            _write_status(_nf_run_dir, {
                "status":        "failed" if _nf_failed else "completed",
                "pid":           os.getpid(),
                "workflow_name": _nf_workflow,
                "question":      state.get("input", ""),
                "started_at":    _nf_started,
                "finished_at":   _dt.datetime.now(_dt.timezone.utc).isoformat(),
                "error":         _nf_error,
            })
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
            run_dir = state.get("run_dir") or get_session_dir() or ""
            final_cmd = wrapper.wrap_command(base_name, raw_cmd, is_workflow=False,
                                             cwd=run_dir)
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
                error_log = _format_error(resp)
                ui_print(f"\n[Executor] Failed:\n{error_log}")
                history.append({"role": "assistant", "content": _msg(
                    f"Execution of {tool_name} failed:\n{error_log}\nI will correct the parameters.",
                    f"我尝试执行了 {tool_name}，但失败了。报错如下：\n{error_log}\n我需要根据这个错误修正参数。",
                )})
                break
            break

    if not (is_local_workflow and next_node == "summarizer"):
        cleanup_temp_scripts()
    return {
        "chat_history": history,
        "next_node": next_node,
        "tool_output": tool_output,
        "run_dir": state.get("run_dir", ""),
        "result_artifacts": result_artifacts,
    }

