#!/usr/bin/env python3
"""
Detached pipeline worker — spawned as an independent subprocess by runner.py.
Survives browser disconnects because it is not tied to the Streamlit session.

Usage:
    python worker/pipeline_worker.py <run_dir>

Reads job.json from run_dir, executes each step sequentially, runs the
workflow-specific analyzer, packages results into a zip, and writes
run_status.json at every stage so the UI can poll progress.
"""
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime

# ── Ensure project root is importable ────────────────────────────────────────
_PROJ_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJ_ROOT not in sys.path:
    sys.path.insert(0, _PROJ_ROOT)

from utils.run_tracker import write_status  # noqa: E402


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_step(cmd_script: str, step_dir: str,
              log_file=None) -> tuple[bool, str]:
    """Run one step, streaming stdout+stderr to log_file in real-time.
    Returns (success, last-3000-chars of combined output)."""
    tail_buf: list[str] = []
    try:
        proc = subprocess.Popen(
            ["bash", cmd_script],
            cwd=step_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge stderr into stdout
            text=True,
            bufsize=1,                  # line-buffered
        )
        for line in proc.stdout:
            print(line, end="", flush=True)   # visible in terminal
            if log_file:
                log_file.write(line)
                log_file.flush()
            tail_buf.append(line)
            if len(tail_buf) > 500:            # keep ~last 500 lines in memory
                tail_buf.pop(0)
        proc.wait()
        tail = "".join(tail_buf)
        tail = tail[-3000:] if len(tail) > 3000 else tail
        return proc.returncode == 0, tail
    except Exception as exc:
        return False, str(exc)


def main():
    run_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        _main(run_dir)
    except Exception:
        tb = traceback.format_exc()
        print(f"[worker] FATAL:\n{tb}", file=sys.stderr)
        if run_dir:
            try:
                write_status(run_dir, {
                    "status":             "failed",
                    "pid":                os.getpid(),
                    "workflow_name":      "",
                    "started_at":         _now_iso(),
                    "finished_at":        _now_iso(),
                    "current_step":       None,
                    "current_step_index": 0,
                    "total_steps":        0,
                    "zip_path":           None,
                    "analysis_images":    [],
                    "text_summary":       "",
                    "warnings":           [],
                    "error":              f"Worker startup crash:\n{tb}",
                })
            except Exception:
                pass
        sys.exit(1)


def _main(run_dir: str):
    if not run_dir:
        print("Usage: pipeline_worker.py <run_dir>", file=sys.stderr)
        sys.exit(1)

    job_path = os.path.join(run_dir, "job.json")

    if not os.path.isfile(job_path):
        print(f"[worker] job.json not found: {job_path}", file=sys.stderr)
        sys.exit(1)

    with open(job_path, encoding="utf-8") as fh:
        job = json.load(fh)

    workflow_name = job.get("workflow_name", "workflow")
    steps         = job.get("steps", [])

    # ── Initial status ────────────────────────────────────────────────────────
    status: dict = {
        "status":             "running",
        "pid":                os.getpid(),
        "workflow_name":      workflow_name,
        "started_at":         _now_iso(),
        "finished_at":        None,
        "current_step":       None,
        "current_step_index": 0,
        "total_steps":        len(steps),
        "zip_path":           None,
        "analysis_images":    [],
        "text_summary":       "",
        "warnings":           [],
        "error":              None,
    }
    write_status(run_dir, status)

    log_path = os.path.join(run_dir, "worker.log")
    with open(log_path, "w", encoding="utf-8", buffering=1) as log:

        def _log(msg: str):
            ts   = datetime.utcnow().strftime("%H:%M:%S")
            line = f"[{ts}] {msg}"
            print(line, flush=True)
            log.write(line + "\n")

        _log(f"[worker] Starting  workflow={workflow_name}  steps={len(steps)}")

        # ── Execute steps ─────────────────────────────────────────────────────
        failed     = False
        fail_error = ""

        for i, step in enumerate(steps):
            tool_name  = step["tool_name"]
            cmd_script = step["cmd_script"]   # absolute path to _run.sh
            step_dir   = step["step_dir"]

            os.makedirs(step_dir, exist_ok=True)

            status["current_step"]       = tool_name
            status["current_step_index"] = i
            write_status(run_dir, status)

            _log(f"[STEP_START] {i+1}/{len(steps)} {tool_name}")
            ok, out = _run_step(cmd_script, step_dir, log_file=log)

            if ok:
                _log(f"[STEP_DONE] {i+1}/{len(steps)} {tool_name}")
            else:
                _log(f"[STEP_FAIL] {i+1}/{len(steps)} {tool_name}\n{out}")
                failed     = True
                fail_error = f"Step {i+1} ({tool_name}) failed:\n{out[-800:]}"
                break

        if failed:
            status["status"]      = "failed"
            status["finished_at"] = _now_iso()
            status["error"]       = fail_error
            write_status(run_dir, status)
            _log(f"[worker] Pipeline FAILED")
            sys.exit(1)

        # ── Workflow analyzer ─────────────────────────────────────────────────
        _log("[worker] All steps done — running analyzer...")

        try:
            from configs.app_config import APP_SNAKE
        except Exception:
            APP_SNAKE = "mod_flow_agent"

        analysis_dir = os.path.join(run_dir, f"{APP_SNAKE}_analysis", workflow_name)
        os.makedirs(analysis_dir, exist_ok=True)

        plot_paths: list[str] = []
        warnings:   list[str] = []
        text_summary           = ""

        try:
            from tools.analyzers.workflow.registry import get_workflow_analyzer
            analyzer = get_workflow_analyzer(workflow_name)
            if analyzer:
                result       = analyzer.analyze(run_dir, analysis_dir)
                plot_paths   = result.get("plot_paths", [])
                warnings     = result.get("warnings", [])
                ts_path      = result.get("text_summary_path", "")
                if ts_path and os.path.isfile(ts_path):
                    with open(ts_path, encoding="utf-8") as fh:
                        text_summary = fh.read()[:4000]
                _log(f"[worker] Analyzer done: {len(plot_paths)} plots, {len(warnings)} warnings")
            else:
                warnings.append(f"No specific analyzer found for workflow: {workflow_name}")
                _log(f"[worker] No analyzer for {workflow_name}")
        except Exception as exc:
            tb = traceback.format_exc()
            warnings.append(f"Analyzer error: {exc}")
            _log(f"[worker] Analyzer error:\n{tb}")


        _log(f"[worker] Skipping zip — raw outputs in: {run_dir}")

        # ── Final status ──────────────────────────────────────────────────────
        status["status"]          = "completed"
        status["finished_at"]     = _now_iso()
        status["current_step"]    = None
        status["zip_path"]        = ""        
        status["run_dir"]         = run_dir  
        status["analysis_images"] = [p for p in plot_paths if os.path.isfile(p)]
        status["text_summary"]    = text_summary
        status["warnings"]        = warnings
        write_status(run_dir, status)
        _log("[worker] Done. ✓")


if __name__ == "__main__":
    main()
