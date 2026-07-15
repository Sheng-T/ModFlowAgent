"""Helpers for local workflow modcaller profiles."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess

from configs import IMAGE_PATH, TOOL_EXEC_ENV


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PROFILE_PATH = os.path.join(_PROJECT_ROOT, "modcaller_profiles.yaml")
_PROFILE_LOCAL_PATH = os.path.join(_PROJECT_ROOT, "modcaller_profiles.local.yaml")


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _load_profile_config() -> dict:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to load modcaller profiles") from exc

    cfg: dict = {}
    for path in (_PROFILE_PATH, _PROFILE_LOCAL_PATH):
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, data)
    return cfg


_PROFILE_CONFIG: dict = _load_profile_config()
PROFILE_VERSION = int(_PROFILE_CONFIG.get("version", 1))

_CONDA_ENVS_CACHE: set[str] | None = None

_IMAGE_TOOL_ALIASES = {
    "pbjasmine": ["pbjasmine", "jasmine"],
    "pb-cpg-tools": ["pb-cpg-tools", "pb_cpg_tools", "pbcpgtools"],
    "fibertools-rs": ["fibertools-rs", "fibertools"],
    "modkit": ["modkit", "ont-modkit"],
}

_MOD_ALIASES = {
    "ont_dna": {
        "cpg": "5mcpg",
        "5mcg": "5mcpg",
        "5mcpg": "5mcpg",
        "5mcg5hmcg": "5mcpg",
        "5hmcg": "5hmcg",
        "5mc": "5mc",
        "5hmc": "5hmc",
        "4mc": "4mc",
        "4mc5mc": "4mc",
        "6ma": "6ma",
        "none": "none",
        "basecallonly": "none",
        "none(basecallonly)": "none",
    },
    "ont_rna": {
        "drach": "m6adrach",
        "m6adrach": "m6adrach",
        "m6a": "m6a",
        "inosine": "inosine",
        "2omea": "2omea",
        "pseu": "pseu",
        "pseudouridine": "pseu",
        "m5c": "m5c",
        "2omeg": "2omeg",
        "none": "none",
        "basecallonly": "none",
        "none(basecallonly)": "none",
    },
    "pacbio_dna": {
        "cpg": "5mcpg",
        "5mcg": "5mcpg",
        "5mcpg": "5mcpg",
        "5mcg5hmcg": "5mcpg",
        "5hmcg": "5hmcg",
        "5mc": "5mc",
        "5hmc": "5hmc",
        "4mc": "4mc",
        "4mc5mc": "4mc",
        "6ma": "6ma",
        "none": "none",
        "basecallonly": "none",
        "none(basecallonly)": "none",
    },
}


def _workflow_data(workflow_name: str) -> dict:
    return _PROFILE_CONFIG.get("workflows", {}).get(workflow_name, {})


def _modcallers_dict(workflow_name: str) -> dict:
    workflow = _workflow_data(workflow_name)
    return workflow.get("modcallers") or workflow.get("callers") or {}


def _list_conda_envs() -> set[str]:
    global _CONDA_ENVS_CACHE
    if _CONDA_ENVS_CACHE is not None:
        return _CONDA_ENVS_CACHE
    try:
        proc = subprocess.run(
            ["conda", "env", "list", "--json"],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(proc.stdout or "{}")
        envs = data.get("envs", [])
        _CONDA_ENVS_CACHE = {os.path.basename(str(path).rstrip("/\\")) for path in envs}
    except Exception:
        _CONDA_ENVS_CACHE = set()
    return _CONDA_ENVS_CACHE


def _entrypoint_exists(profile: dict) -> bool:
    entrypoint = (profile.get("entrypoint") or "").strip()
    if not entrypoint:
        return True
    parts = entrypoint.split()
    if not parts:
        return True
    exe = parts[0]
    if os.path.isabs(exe):
        return os.path.exists(exe)
    if exe in ("python", "python3"):
        if len(parts) >= 2:
            script = parts[1]
            if os.path.isabs(script):
                return os.path.exists(script)
            workdir = (profile.get("workdir") or "").strip()
            if workdir:
                return os.path.exists(os.path.join(workdir, script))
        return shutil.which(exe) is not None
    if shutil.which(exe):
        return True
    workdir = (profile.get("workdir") or "").strip()
    if workdir:
        candidate = os.path.join(workdir, exe)
        return os.path.exists(candidate)
    return False


def _entrypoint_requires_host_check(profile: dict) -> bool:
    entrypoint = (profile.get("entrypoint") or "").strip()
    if not entrypoint:
        return False
    parts = entrypoint.split()
    if not parts:
        return False
    exe = parts[0]
    if os.path.isabs(exe):
        return True
    if exe in ("python", "python3") and len(parts) >= 2:
        script = parts[1]
        if os.path.isabs(script):
            return True
        workdir = (profile.get("workdir") or "").strip()
        if workdir:
            return True
    return False


def _resolve_tool_runtime_image(tool_name: str) -> str | None:
    base_store = os.path.expanduser(IMAGE_PATH["image_store"])
    aliases = _IMAGE_TOOL_ALIASES.get(tool_name, [tool_name])

    for alias in aliases:
        tool_dir = os.path.join(base_store, alias)
        if not os.path.isdir(tool_dir):
            continue
        img_files = [f for f in os.listdir(tool_dir) if f.endswith((".img", ".sif"))]
        if not img_files:
            continue
        img_files.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
        return os.path.join(tool_dir, img_files[0])

    methylong_cache = os.path.join(base_store, "workflow", "methylong")
    if os.path.isdir(methylong_cache):
        normalized_aliases = [a.lower().replace("-", "").replace("_", "") for a in aliases]
        candidates = []
        for name in os.listdir(methylong_cache):
            if not name.endswith((".img", ".sif")):
                continue
            norm_name = name.lower().replace("-", "").replace("_", "")
            if any(alias in norm_name for alias in normalized_aliases):
                candidates.append(name)
        if candidates:
            candidates.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
            return os.path.join(methylong_cache, candidates[0])
    return None


def is_modcaller_available(workflow_name: str, modcaller_name: str) -> tuple[bool, str]:
    profile = get_modcaller_profile(workflow_name, modcaller_name)
    if not profile:
        return False, "profile not found"
    runtime = profile.get("runtime", {})
    runtime_type = runtime.get("type", "")
    require_host_entrypoint = True
    if runtime_type == "conda":
        env_name = (runtime.get("env_name") or "").strip()
        if not env_name:
            return False, "missing conda env_name"
        if env_name not in _list_conda_envs():
            return False, f"conda env '{env_name}' not found"
        # For conda runtimes, the entrypoint is expected to be resolved after
        # activating that environment, so we should not require it to exist in
        # the host process PATH.
        require_host_entrypoint = False
    elif runtime_type == "singularity":
        image = os.path.expanduser((runtime.get("image") or "").strip())
        if not image or not os.path.isfile(image):
            return False, f"singularity image not found: {image or '<empty>'}"
        require_host_entrypoint = False
    elif runtime_type == "tool":
        tool_name = (runtime.get("tool_name") or modcaller_name).strip()
        has_image = bool(_resolve_tool_runtime_image(tool_name))
        has_exec_env = bool(TOOL_EXEC_ENV)
        if not has_image and not has_exec_env:
            return False, f"tool runtime '{tool_name}' has no image and no TOOL_EXEC_ENV fallback"
        require_host_entrypoint = False
    elif runtime_type == "script":
        script_path = os.path.expanduser((runtime.get("script_path") or "").strip())
        if not script_path or not os.path.isfile(script_path):
            return False, f"script runtime not found: {script_path or '<empty>'}"
    else:
        return False, f"unsupported runtime type '{runtime_type}'"

    workdir = os.path.expanduser((profile.get("workdir") or "").strip())
    workdir_ok = (not workdir) or os.path.isdir(workdir)
    entrypoint_ok = True if not require_host_entrypoint else _entrypoint_exists(profile)

    # workdir is optional metadata, not a hard requirement by itself.
    # For conda-installed tools (for example pip-installed CLIs inside a conda
    # env), we should not hide a modcaller just because there is no workdir or
    # because the entrypoint is not visible in the host PATH before activation.
    if require_host_entrypoint:
        if not entrypoint_ok and workdir and not workdir_ok:
            return False, f"workdir not found: {workdir}"
        if not entrypoint_ok and not workdir_ok:
            return False, (
                f"entrypoint not found: {profile.get('entrypoint', '')}; "
                f"workdir not found: {workdir}"
            )
        if not entrypoint_ok and not workdir:
            return False, f"entrypoint not found: {profile.get('entrypoint', '')}"
    else:
        if workdir and not workdir_ok:
            return False, f"workdir not found: {workdir}"
        if _entrypoint_requires_host_check(profile) and not _entrypoint_exists(profile):
            return False, f"entrypoint not found: {profile.get('entrypoint', '')}"
    return True, ""


def get_workflow_profile(workflow_name: str) -> dict:
    return copy.deepcopy(_workflow_data(workflow_name))


def get_modcaller_profile(workflow_name: str, modcaller_name: str) -> dict:
    return copy.deepcopy(_modcallers_dict(workflow_name).get(modcaller_name, {}))


def get_caller_profile(workflow_name: str, caller_name: str) -> dict:
    return get_modcaller_profile(workflow_name, caller_name)


def list_available_modcallers(workflow_name: str) -> list[dict]:
    out: list[dict] = []
    for name, profile in _modcallers_dict(workflow_name).items():
        available, reason = is_modcaller_available(workflow_name, name)
        enriched = copy.deepcopy(profile)
        enriched["name"] = name
        enriched["available"] = available
        enriched["unavailable_reason"] = reason
        out.append(enriched)
    out.sort(key=lambda item: (-int(item.get("priority", 0)), item["name"]))
    return out


def list_workflow_modification_types(workflow_name: str, available_only: bool = True) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    profiles = list_available_modcallers(workflow_name) if available_only else [
        {"name": name, **copy.deepcopy(profile)}
        for name, profile in _modcallers_dict(workflow_name).items()
    ]
    for profile in profiles:
        if available_only and not profile.get("available"):
            continue
        for mod in profile.get("supported_modification_types", []):
            if mod not in seen:
                seen.add(mod)
                ordered.append(mod)
    if ordered:
        return ordered
    if available_only:
        return list_workflow_modification_types(workflow_name, available_only=False)
    workflow = _workflow_data(workflow_name)
    default_mod = workflow.get("default_modification_type", "none")
    return [default_mod, "none"] if default_mod != "none" else ["none"]


def get_default_modification_type(workflow_name: str) -> str:
    workflow = _workflow_data(workflow_name)
    return workflow.get("default_modification_type", "none")


def normalize_modification_type(workflow_name: str, value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return get_default_modification_type(workflow_name)
    lowered = raw.lower().replace("-", "").replace("_", "").replace(" ", "")
    alias = _MOD_ALIASES.get(workflow_name, {})
    if lowered in alias:
        return alias[lowered]
    for opt in list_workflow_modification_types(workflow_name, available_only=False):
        if raw.lower() == opt.lower():
            return opt
    return get_default_modification_type(workflow_name)


def resolve_modcaller(workflow_name: str, modification_type: str) -> str:
    workflow = _workflow_data(workflow_name)
    profiles = list_available_modcallers(workflow_name)
    if not profiles:
        return ""
    canonical = normalize_modification_type(workflow_name, modification_type)
    fallback = workflow.get("fallback_modcaller") or workflow.get("fallback_caller") or ""
    candidates: list[tuple[int, str]] = []
    for profile in profiles:
        if not profile.get("available"):
            continue
        supported = profile.get("supported_modification_types", [])
        name = profile["name"]
        if canonical in supported or (canonical == "none" and fallback == name):
            candidates.append((int(profile.get("priority", 0)), name))
    if not candidates:
        fallback_ok, _ = is_modcaller_available(workflow_name, fallback)
        # Only use the workflow fallback when the request is effectively
        # unspecified/empty. If the user asked for an unsupported modification
        # type, return empty so the UI can surface "not supported" instead of
        # silently switching callers.
        if (not modification_type or canonical == get_default_modification_type(workflow_name)) and fallback and fallback_ok:
            return fallback
        return ""
    if fallback:
        for _, name in candidates:
            if name == fallback:
                return fallback
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][1]


def resolve_caller(workflow_name: str, modification_type: str) -> str:
    return resolve_modcaller(workflow_name, modification_type)


def get_modcaller_display_name(workflow_name: str, modcaller_name: str) -> str:
    profile = get_modcaller_profile(workflow_name, modcaller_name)
    return profile.get("display_name", modcaller_name)


def evaluate_modcaller_request(
    workflow_name: str,
    modification_type: str,
    requested_modcaller: str = "",
) -> dict:
    canonical_mod = normalize_modification_type(workflow_name, modification_type)
    requested = (requested_modcaller or "").strip()
    recommended = resolve_modcaller(workflow_name, canonical_mod)
    result = {
        "canonical_modification_type": canonical_mod,
        "requested_modcaller": requested,
        "resolved_modcaller": "",
        "recommended_modcaller": recommended,
        "blocking_reason": "",
    }

    if not requested:
        result["resolved_modcaller"] = recommended
        return result

    profile = get_modcaller_profile(workflow_name, requested)
    if not profile:
        rec = get_modcaller_display_name(workflow_name, recommended) if recommended else ""
        rec_tail = f" Recommended compatible modcaller: {rec} ({recommended})." if recommended else ""
        result["blocking_reason"] = (
            f"Requested modcaller '{requested}' is not configured for workflow '{workflow_name}'."
            f"{rec_tail}"
        )
        return result

    supported = profile.get("supported_modification_types", [])
    if canonical_mod not in supported and canonical_mod != "none":
        supported_text = ", ".join(supported) if supported else "none"
        rec = get_modcaller_display_name(workflow_name, recommended) if recommended else ""
        rec_tail = f" Recommended compatible modcaller: {rec} ({recommended})." if recommended else ""
        result["blocking_reason"] = (
            f"Requested modcaller '{requested}' does not support modification type '{canonical_mod}' "
            f"for workflow '{workflow_name}'. Supported types: {supported_text}.{rec_tail}"
        )
        return result

    available, reason = is_modcaller_available(workflow_name, requested)
    if not available:
        rec = get_modcaller_display_name(workflow_name, recommended) if recommended else ""
        rec_tail = f" Recommended compatible modcaller: {rec} ({recommended})." if recommended else ""
        result["blocking_reason"] = (
            f"Requested modcaller '{requested}' is unavailable: {reason}.{rec_tail}"
        )
        return result

    result["resolved_modcaller"] = requested
    return result


def build_tool_sequence(workflow_name: str, modcaller_name: str, modification_type: str, reference: str) -> list[str]:
    modcaller = get_modcaller_profile(workflow_name, modcaller_name)
    if not modcaller:
        return []
    seq = list(modcaller.get("caller_steps", []))
    canonical_mod = normalize_modification_type(workflow_name, modification_type)
    post = modcaller.get("postprocess", {})
    wants_modkit = canonical_mod != "none" and bool(
        post.get("modkit_pileup") or post.get("modkit_extract")
    )

    def _append_once(step_name: str) -> None:
        if step_name not in seq:
            seq.append(step_name)

    def _insert_after_once(anchor_step: str, step_name: str) -> None:
        if step_name in seq:
            return
        if anchor_step not in seq:
            seq.append(step_name)
            return
        anchor_idx = seq.index(anchor_step)
        insert_idx = anchor_idx + 1
        while insert_idx < len(seq) and seq[insert_idx] in ("samtools_sort", "samtools_index"):
            insert_idx += 1
        seq.insert(insert_idx, step_name)

    # Dorado basecalling almost always needs a sorted and indexed BAM afterward.
    # Make that a platform default instead of forcing every profile author to
    # repeat the same two generic steps.
    if "dorado_basecaller" in seq:
        _insert_after_once("dorado_basecaller", "samtools_sort")
        _insert_after_once("samtools_sort", "samtools_index")

    if (
        workflow_name == "pacbio_dna"
        and canonical_mod == "5mcpg"
        and reference
        and modcaller.get("pileup_method") == "pb_cpg_tools"
    ):
        _append_once("samtools_faidx")
        _append_once("pb_cpg_tools_run")

    if (
        workflow_name == "pacbio_dna"
        and modcaller_name == "ccsmeth"
        and canonical_mod == "5mcpg"
        and reference
    ):
        _append_once("samtools_faidx")
        _append_once("ccsmeth_callfreqb_run")

    if post.get("samtools_sort"):
        _append_once("samtools_sort")
    if post.get("samtools_index"):
        _append_once("samtools_index")
    if reference and wants_modkit and post.get("samtools_faidx"):
        _append_once("samtools_faidx")
    if wants_modkit:
        if reference and post.get("modkit_pileup"):
            _append_once("modkit_pileup")
        if post.get("modkit_extract"):
            _append_once("modkit_extract")
    return seq
