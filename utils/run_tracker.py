"""
Persistent run_status.json helper for detached pipeline workers.

Schema of run_dir/run_status.json:
  status            "pending" | "running" | "completed" | "failed"
  pid               int | null
  workflow_name     str
  started_at        ISO-8601 str | null
  finished_at       ISO-8601 str | null
  current_step      str | null
  current_step_index int   (0-based)
  total_steps       int
  zip_path          str | null
  analysis_images   list[str]
  text_summary      str
  warnings          list[str]
  error             str | null
"""
from __future__ import annotations

import json
import os
from typing import Optional

STATUS_FILE = "run_status.json"


def write_status(run_dir: str, data: dict) -> None:
    """Atomically write run_status.json into run_dir."""
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, STATUS_FILE)
    tmp  = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def read_status(run_dir: str) -> Optional[dict]:
    """Return parsed run_status.json, or None if absent / corrupt."""
    path = os.path.join(run_dir, STATUS_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def find_session_runs(session_dir: str) -> list[dict]:
    """
    Scan session_dir for run subdirectories.
    Dirs with run_status.json return full metadata; dirs without return path-only entries.
    Returns list sorted by started_at desc (status dirs first, then path-only by name).
    """
    results = []
    if not session_dir or not os.path.isdir(session_dir):
        return results
    try:
        for entry in os.scandir(session_dir):
            if not entry.is_dir():
                continue
            s = read_status(entry.path)
            if s:
                results.append({"run_dir": entry.path, "name": entry.name, **s})
            else:
                # No status file — include as a path-only entry so users can still find outputs
                results.append({
                    "run_dir":       entry.path,
                    "name":          entry.name,
                    "status":        "unknown",
                    "workflow_name": "",
                    "question":      "",
                    "started_at":    None,
                })
    except PermissionError:
        pass
    # Status-tracked runs first (sorted by time desc), then path-only dirs by name
    results.sort(key=lambda x: (x.get("started_at") or "") == "", reverse=False)
    results.sort(key=lambda x: x.get("started_at") or "", reverse=True)
    return results


def is_pid_alive(pid: Optional[int]) -> bool:
    """Return True if process pid is still running."""
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
