"""Shared helpers for profile-driven local workflow steps."""
from __future__ import annotations

import json
import os
import re
import subprocess
import string
from pathlib import Path

from configs.runtime_config import TOOL_THREADS
from tools.workflow.caller_profiles import get_modcaller_profile
from utils.runner_utils import _find_free_gpu


def skip_if_exists(output_path: str, cmd: str) -> str:
    """Wrap cmd so it is skipped when output_path already exists."""
    return f'[ -f "{output_path}" ] && echo "[Resume] {os.path.basename(output_path)} exists, skipping" || ( {cmd} )'


def get_modcaller_name(prereq: dict) -> str:
    return (prereq.get("modcaller") or prereq.get("caller") or "").strip()


def get_modcaller_runtime_base_tool(workflow_name: str, prereq: dict) -> str:
    modcaller_name = get_modcaller_name(prereq)
    profile = get_modcaller_profile(workflow_name, modcaller_name) if modcaller_name else {}
    runtime = profile.get("runtime", {})
    runtime_type = runtime.get("type", "")
    if runtime_type == "tool":
        return (runtime.get("tool_name") or modcaller_name or "workflow").strip()
    base_tool = (profile.get("base_tool") or "").strip()
    if base_tool:
        return base_tool
    entrypoint = (profile.get("entrypoint") or "").strip()
    if entrypoint:
        token = entrypoint.split()[0]
        return os.path.basename(token)
    return modcaller_name or "workflow"


def _first_existing(mapping: list[tuple[str, str]]) -> str:
    for _, path in mapping:
        if path:
            return path
    return ""


def get_known_outputs(all_step_dirs: dict, data_file: str = "", reference: str = "", step_dir: str = "") -> dict:
    outputs = {
        "data_file": data_file,
        "reference": reference,
        "run_dir": os.path.dirname(step_dir) if step_dir else "",
        "step_dir": step_dir,
        "calls_bam": "",
        "sorted_bam": "",
        "aligned_bam": "",
        "modcaller_bam": "",
        "bam": "",
    }
    if all_step_dirs.get("dorado_basecaller"):
        outputs["calls_bam"] = os.path.join(all_step_dirs["dorado_basecaller"], "calls.bam")
    if all_step_dirs.get("samtools_sort"):
        outputs["sorted_bam"] = os.path.join(all_step_dirs["samtools_sort"], "sorted.bam")
    if all_step_dirs.get("pbmm2_align"):
        outputs["aligned_bam"] = os.path.join(all_step_dirs["pbmm2_align"], "aligned.bam")
    if all_step_dirs.get("modcaller_run"):
        outputs["modcaller_bam"] = os.path.join(all_step_dirs["modcaller_run"], "modcaller.bam")
    outputs["bam"] = _first_existing([
        ("sorted_bam", outputs["sorted_bam"]),
        ("aligned_bam", outputs["aligned_bam"]),
        ("modcaller_bam", outputs["modcaller_bam"]),
        ("calls_bam", outputs["calls_bam"]),
        ("data_file", data_file if str(data_file).lower().endswith(".bam") else ""),
    ])
    return outputs


def resolve_input_bam(all_step_dirs: dict, data_file: str = "", prefer_modcaller: bool = False) -> str:
    known = get_known_outputs(all_step_dirs, data_file=data_file)
    if prefer_modcaller:
        return _first_existing([
            ("modcaller_bam", known["modcaller_bam"]),
            ("aligned_bam", known["aligned_bam"]),
            ("sorted_bam", known["sorted_bam"]),
            ("calls_bam", known["calls_bam"]),
            ("data_file", data_file if str(data_file).lower().endswith(".bam") else ""),
        ])
    return _first_existing([
        ("aligned_bam", known["aligned_bam"]),
        ("sorted_bam", known["sorted_bam"]),
        ("modcaller_bam", known["modcaller_bam"]),
        ("calls_bam", known["calls_bam"]),
        ("data_file", data_file if str(data_file).lower().endswith(".bam") else ""),
    ])


class _SafeFormatDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _render_template_text(template_text: str, placeholders: dict) -> str:
    return string.Formatter().vformat(template_text, (), _SafeFormatDict(placeholders))


def _render_known_placeholders_only(template_text: str, placeholders: dict) -> str:
    """Replace only known {name} placeholders and leave other braces untouched.

    This is safer for hook code snippets that legitimately contain Python dict
    braces or shell JSON fragments.
    """
    rendered = str(template_text)
    for key, value in sorted(placeholders.items(), key=lambda kv: len(str(kv[0])), reverse=True):
        rendered = rendered.replace("{" + str(key) + "}", str(value))
    return rendered


def _resolve_device(raw_device: str) -> str:
    raw_device = (raw_device or "auto").strip() or "auto"
    if raw_device != "auto":
        return raw_device
    return _find_free_gpu(min_free_mb=10000) or "cpu"


def _base_device_placeholders(resolved_device: str) -> dict:
    gpu_ids: list[str] = []
    if resolved_device.startswith("cuda:"):
        gpu_ids = [part.strip() for part in resolved_device.split(":", 1)[1].split(",") if part.strip()]

    return {
        "device": resolved_device,
        "device_gpu_count": str(len(gpu_ids)),
        "device_gpu_pool": " ".join(gpu_ids),
        "device_first_gpu": gpu_ids[0] if gpu_ids else "",
        "device_is_gpu": "true" if gpu_ids else "false",
        "device_gpu_ids_csv": ",".join(gpu_ids),
    }


def _run_python_hook(code: str, placeholders: dict) -> dict:
    rendered_code = _render_known_placeholders_only(code, placeholders)
    safe_builtins = {
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "dict": dict,
        "list": list,
        "min": min,
        "max": max,
        "sum": sum,
        "range": range,
    }
    scope = {"result": None}
    exec(rendered_code, {"__builtins__": safe_builtins}, scope)
    result = scope.get("result")
    if result is None:
        raise ValueError("python device transform must assign a dict to `result`")
    if not isinstance(result, dict):
        raise ValueError("python hook `result` must be a dict")
    return {str(k): str(v) for k, v in result.items()}


def _run_bash_hook(code: str, placeholders: dict) -> dict:
    rendered_code = _render_known_placeholders_only(code, placeholders)
    env = dict(os.environ)
    env.update({
        "DEVICE": placeholders["device"],
        "DEVICE_GPU_COUNT": placeholders["device_gpu_count"],
        "DEVICE_GPU_POOL": placeholders["device_gpu_pool"],
        "DEVICE_FIRST_GPU": placeholders["device_first_gpu"],
        "DEVICE_IS_GPU": placeholders["device_is_gpu"],
        "DEVICE_GPU_IDS_CSV": placeholders["device_gpu_ids_csv"],
    })
    proc = subprocess.run(
        ["bash", "-lc", rendered_code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        raise ValueError((proc.stderr or proc.stdout or "").strip() or "bash hook failed")
    raw = (proc.stdout or "").strip()
    if not raw:
        raise ValueError("bash hook produced empty stdout; expected JSON object")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("bash hook stdout must be a JSON object")
    return {str(k): str(v) for k, v in parsed.items()}


def _load_hook_code(hook_cfg: dict) -> str:
    code = (hook_cfg.get("code") or "").strip()
    if code:
        return code
    script_path = (hook_cfg.get("script_path") or "").strip()
    if not script_path:
        return ""
    path = Path(os.path.expanduser(script_path))
    if not path.is_file():
        raise ValueError(f"hook script not found: {script_path}")
    return path.read_text(encoding="utf-8")


def _normalize_hook_result(raw: dict) -> dict:
    result = {
        "placeholders": {},
        "command_prefix": "",
        "command_suffix": "",
    }
    if "placeholders" in raw and isinstance(raw["placeholders"], dict):
        result["placeholders"] = {str(k): str(v) for k, v in raw["placeholders"].items()}
    else:
        reserved = {"command_prefix", "command_suffix"}
        result["placeholders"] = {
            str(k): str(v)
            for k, v in raw.items()
            if k not in reserved
        }
    if "command_prefix" in raw:
        result["command_prefix"] = str(raw["command_prefix"])
    if "command_suffix" in raw:
        result["command_suffix"] = str(raw["command_suffix"])
    return result


def _execute_hook(hook_cfg: dict, placeholders: dict) -> dict:
    mode = (hook_cfg.get("mode") or "python").strip().lower()
    code = _load_hook_code(hook_cfg)
    if not code:
        return {"placeholders": {}, "command_prefix": "", "command_suffix": ""}
    if mode == "python":
        raw = _run_python_hook(code, placeholders)
    elif mode == "bash":
        raw = _run_bash_hook(code, placeholders)
    else:
        raise ValueError(f"unsupported hook mode '{mode}'")
    return _normalize_hook_result(raw)


def _legacy_pre_hook_from_profile(profile: dict) -> dict | None:
    mode = (profile.get("device_transform") or "passthrough").strip().lower()
    if mode in ("", "passthrough"):
        return None
    code = (profile.get("device_transform_code") or "").strip()
    if not code:
        return None
    return {
        "mode": mode,
        "code": code,
        "required": bool(profile.get("require_gpu")),
    }


def render_command_template(
    workflow_name: str,
    prereq: dict,
    step_dir: str,
    all_step_dirs: dict,
    data_path: dict,
) -> tuple[str, str]:
    modcaller_name = get_modcaller_name(prereq)
    profile = get_modcaller_profile(workflow_name, modcaller_name) if modcaller_name else {}
    command_template = (profile.get("command_template") or profile.get("command_example") or "").strip()
    if not command_template:
        return (
            "workflow",
            f"error: modcaller '{modcaller_name or '<empty>'}' has no command_template/command_example configured",
        )

    reference = prereq.get("reference", "") or ""
    data_file = prereq.get("data_file", "") or ""
    raw_device = (prereq.get("device", "auto") or "auto").strip() or "auto"
    resolved_device = _resolve_device(raw_device)
    known = get_known_outputs(all_step_dirs, data_file=data_file, reference=reference, step_dir=step_dir)
    device_placeholders = _base_device_placeholders(resolved_device)
    if profile.get("require_gpu") and device_placeholders.get("device_is_gpu") != "true":
        return (
            "workflow",
            f"error: modcaller '{modcaller_name}' requires a GPU device, but no CUDA device was resolved from the current setting",
        )
    placeholders = {
        "entrypoint": profile.get("entrypoint", ""),
        "data_file": data_file,
        "reference": reference,
        "threads": TOOL_THREADS,
        "run_dir": known["run_dir"],
        "step_dir": step_dir,
        "modification_type": prereq.get("modification_type", ""),
        "resume_run_dir": prereq.get("resume_run_dir", ""),
        "calls_bam": known["calls_bam"],
        "sorted_bam": known["sorted_bam"],
        "aligned_bam": known["aligned_bam"],
        "modcaller_bam": known["modcaller_bam"] or os.path.join(step_dir, "modcaller.bam"),
        "bam": known["bam"],
        "model_dir": data_path.get("dorado_models", ""),
        "pipeline_dir": data_path.get("pipeline_dir", ""),
        "base_data_dir": data_path.get("base_data_dir", ""),
    }

    if workflow_name == "pacbio_dna":
        caller_steps = list(profile.get("caller_steps", []))
        if "pbmm2_align" in caller_steps and "modcaller_run" in caller_steps:
            pbmm2_before_modcaller = caller_steps.index("pbmm2_align") < caller_steps.index("modcaller_run")
            if pbmm2_before_modcaller:
                placeholders["bam"] = (
                    known["aligned_bam"]
                    or known["sorted_bam"]
                    or known["bam"]
                    or data_file
                )
            else:
                placeholders["bam"] = data_file if str(data_file).lower().endswith(".bam") else (
                    known["sorted_bam"]
                    or known["calls_bam"]
                    or known["bam"]
                )

    placeholders.update(device_placeholders)
    template_vars = profile.get("template_vars", {})
    if isinstance(template_vars, dict):
        rendered_vars = {}
        for key, value in template_vars.items():
            rendered_vars[str(key)] = _render_known_placeholders_only(str(value), placeholders)
        placeholders.update(rendered_vars)
    warning_msgs: list[str] = []

    pre_hook = profile.get("modcaller_pre") or _legacy_pre_hook_from_profile(profile)
    if isinstance(pre_hook, dict):
        try:
            pre_result = _execute_hook(pre_hook, placeholders)
            placeholders.update(pre_result.get("placeholders", {}))
            pre_prefix = (pre_result.get("command_prefix") or "").strip()
        except Exception as exc:
            if pre_hook.get("required"):
                return ("workflow", f"error: modcaller '{modcaller_name}' pre-hook failed: {exc}")
            warning_msgs.append(f"[ModcallerWarning] pre-hook failed: {exc}")
            pre_prefix = ""
    else:
        pre_prefix = ""

    raw_cmd = string.Formatter().vformat(command_template, (), _SafeFormatDict(placeholders)).strip()
    unresolved = sorted({name for _, name, _, _ in string.Formatter().parse(raw_cmd) if name})
    if unresolved:
        return ("workflow", f"error: unresolved placeholders for modcaller '{modcaller_name}': {unresolved}")

    post_hook = profile.get("modcaller_post")
    if isinstance(post_hook, dict):
        try:
            post_result = _execute_hook(post_hook, placeholders)
            post_suffix = (post_result.get("command_suffix") or "").strip()
        except Exception as exc:
            if post_hook.get("required"):
                return ("workflow", f"error: modcaller '{modcaller_name}' post-hook failed: {exc}")
            warning_msgs.append(f"[ModcallerWarning] post-hook failed: {exc}")
            post_suffix = ""
    else:
        post_suffix = ""

    command_parts = []
    if warning_msgs:
        for msg in warning_msgs:
            command_parts.append(f'echo "{msg}"')
    if pre_prefix:
        command_parts.append(pre_prefix)
    command_parts.append(raw_cmd)
    if post_suffix:
        command_parts.append(post_suffix)
    final_cmd = " && ".join(part for part in command_parts if part)

    done_flag = os.path.join(step_dir, ".modcaller_run.done")
    wrapped = skip_if_exists(done_flag, f"{final_cmd} && touch \"{done_flag}\"")
    return get_modcaller_runtime_base_tool(workflow_name, prereq), wrapped


def build_pbmm2_align_command(
    prereq: dict,
    step_dir: str,
    all_step_dirs: dict,
    prefer_modcaller: bool = True,
) -> tuple[str, str] | None:
    reference = prereq.get("reference", "") or ""
    data_file = prereq.get("data_file", "") or ""
    if not reference:
        return None

    known = get_known_outputs(all_step_dirs, data_file=data_file, reference=reference, step_dir=step_dir)
    if prefer_modcaller:
        input_bam = _first_existing([
            ("modcaller_bam", known["modcaller_bam"]),
            ("sorted_bam", known["sorted_bam"]),
            ("calls_bam", known["calls_bam"]),
            ("data_file", data_file if str(data_file).lower().endswith(".bam") else ""),
        ])
    else:
        input_bam = _first_existing([
            ("sorted_bam", known["sorted_bam"]),
            ("calls_bam", known["calls_bam"]),
            ("data_file", data_file if str(data_file).lower().endswith(".bam") else ""),
        ])
    if not input_bam:
        return ("workflow", "error: pbmm2_align could not resolve an input BAM")

    out_bam = os.path.join(step_dir, "aligned.bam")

    raw = (
        f'pbmm2 align "{reference}" "{input_bam}" "{out_bam}" '
        f'--preset CCS --sort --num-threads {TOOL_THREADS}'
    )
    return ("pbmm2", skip_if_exists(out_bam, raw))
