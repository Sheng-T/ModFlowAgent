"""
前置文件生成节点。

对于需要 samplesheet 等前置文件的 workflow，用 LLM 根据用户上传文件
自动生成文件内容，存入 state["pre_files"]，供审查和执行使用。
"""
import importlib
import os


def _skip_validation() -> bool:
    return os.environ.get("ABLATION_NO_VALIDATION", "0") == "1"


from agent_graph.state import AgentState
from agent_graph.prompts.workflow_prompts import build_prereq_prompt
from utils.workflow_prerequisites import get_prereqs
from utils.llm_utils import get_llm_instance
from utils.lang_utils import get_lang
from utils.user_context import get_session_dir
from utils.ui_logger import ui_print


def _get_workflow_prereq_prompt(workflow: str):
    """Return the workflow-specific prereq prompt module, or None if not found."""
    try:
        return importlib.import_module(f"agent_graph.prompts.workflows.{workflow}.prereq_prompt")
    except ModuleNotFoundError:
        return None


def _get_workflow_validator(workflow: str):
    """Return the workflow-specific validator module, or None if not found."""
    try:
        return importlib.import_module(f"tools.workflow.nf.{workflow}.validator")
    except ModuleNotFoundError:
        return None


def _list_session_files() -> list[str]:
    """Return full absolute paths of all files in session_dir.
    Symlinks to files are included directly; symlinks to directories are expanded one level."""
    session_dir = get_session_dir()
    if not session_dir or not os.path.isdir(session_dir):
        return []
    result = []
    for e in os.scandir(session_dir):
        if e.is_file(follow_symlinks=True):
            result.append(e.path)
        elif e.is_dir(follow_symlinks=True) and os.path.islink(e.path):
            result.extend(
                se.path for se in os.scandir(e.path)
                if se.is_file(follow_symlinks=True)
            )
    return result



def generate_prereqs_node(state: AgentState) -> dict:
    import re
    import csv
    import io

    selected_workflow = state.get("selected_workflow", "")
    prereqs = get_prereqs(selected_workflow)

    if not prereqs:
        return {}

    user_input = state.get("input", "")
    user_feedback = state.get("user_feedback", "")
    lang = get_lang()
    llm = get_llm_instance(is_planner=True)

    # If the user explicitly provided file paths in their message, use only those
    # paths — do not include unrelated historical files from the session directory.
    # Fall back to all session files only when no explicit paths are present.
    explicit_paths = _extract_paths_from_input(user_input)
    if explicit_paths:
        uploaded_files = explicit_paths
    else:
        uploaded_files = _list_session_files()

    wf_prompt_mod = _get_workflow_prereq_prompt(selected_workflow)
    wf_validator   = _get_workflow_validator(selected_workflow)

    MAX_RETRIES = 3

    def _parse_content(raw) -> str:
        content = raw if isinstance(raw, str) else raw.content
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
        content = re.sub(r"<think>.*",          "", content, flags=re.DOTALL)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0].strip()
        return content

    def _validate_content(content: str, prereq: dict) -> tuple[bool, str]:
        if not content:
            return False, "content is empty"
        file_type = prereq.get("type", "")
        if file_type == "csv":
            all_cols      = prereq.get("columns", [])
            optional_cols = set(prereq.get("optional_columns", []))
            required_cols = [c for c in all_cols if c not in optional_cols]
            try:
                reader = csv.DictReader(io.StringIO(content))
                header = reader.fieldnames or []
                missing_cols = [c for c in all_cols if c not in header]
                if missing_cols:
                    return False, f"missing columns: {missing_cols} (got header: {header})"
                data_rows = [r for r in reader if any(v.strip() for v in r.values())]
                # Allow header-only template (no data rows) — user will fill manually
                for row_idx, row in enumerate(data_rows, 1):
                    empty_cols = [c for c in required_cols if not (row.get(c) or "").strip()]
                    if empty_cols:
                        return False, f"row {row_idx} has empty values for required columns: {empty_cols}"
            except Exception as exc:
                return False, f"CSV parse error: {exc}"
        return True, ""

    pre_files = []
    for prereq in prereqs:
        filename = prereq["filename"]
        print(f"[PrereqGenerator] Generating {filename}...")

        # Build prompt: prefer workflow-specific module, fall back to generic
        if wf_prompt_mod and hasattr(wf_prompt_mod, "build_prereq_prompt"):
            prompt = wf_prompt_mod.build_prereq_prompt(
                prereq, uploaded_files, user_input, lang=lang, feedback=user_feedback,
            )
        else:
            prompt = build_prereq_prompt(prereq, uploaded_files, user_input, lang)

        content = ""
        fail_reason = ""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                raw = llm.invoke(prompt)
                content = _parse_content(raw)
                ok, fail_reason = _validate_content(content, prereq)
                if ok:
                    print(f"[PrereqGenerator] {filename} validated (attempt {attempt})")
                    break
                if _skip_validation():
                    break  # ablation: skip retry, accept LLM output as-is
                print(f"[PrereqGenerator] {filename} validation failed (attempt {attempt}): {fail_reason}, retrying...")
                content = ""
            except Exception as e:
                print(f"[PrereqGenerator] Attempt {attempt} exception: {e}")
                content = ""

        if not content:
            print(f"[PrereqGenerator] ERROR: {filename} still invalid after {MAX_RETRIES} attempts: {fail_reason}, skipping")
            continue

        # Workflow-specific post-processing: path fixing
        if wf_validator and hasattr(wf_validator, "fix_paths") and not _skip_validation():
            content = wf_validator.fix_paths(content, uploaded_files)

        pre_files.append({"filename": filename, "content": content})

    # Workflow-specific validation (e.g. MM/ML tag check, DMR groups)
    samplesheet_issues: list[dict] = []
    if wf_validator and hasattr(wf_validator, "validate_samplesheet") and pre_files and not _skip_validation():
        for pf in pre_files:
            issues = wf_validator.validate_samplesheet(pf["content"], user_input)
            samplesheet_issues.extend(issues)
        if samplesheet_issues:
            print(f"[PrereqGenerator] Samplesheet issues: {samplesheet_issues}")

    return {"pre_files": pre_files, "user_feedback": "", "samplesheet_issues": samplesheet_issues}


def human_prereq_reviewer_node(state: AgentState) -> dict:  # noqa: ARG001
    """
    Pass-through interrupt node between prereq_generator and param_generator.
    The graph pauses BEFORE this node so the UI can render an editable samplesheet.
    The UI calls app.update_state({"pre_files": edited}) then resumes — this node
    just forwards state unchanged.
    """
    _ = state  # intentionally unused; graph state is passed through unchanged
    return {}


# ── Local workflow prereq nodes ────────────────────────────────────────────────

def _inspect_pod5_kit(file_path: str) -> dict:
    """
    Try to read flowcell/kit metadata from a pod5 file.
    Returns {"flow_cell": str, "kit": str, "is_rna004": bool} or {} on failure.
    """
    try:
        import pod5  # type: ignore[import]
        with pod5.Reader(file_path) as reader:
            for read in reader.reads():
                ri = read.run_info
                flow_cell = getattr(ri, "flow_cell_product_code", "") or ""
                kit = getattr(ri, "sequencing_kit", "") or ""
                is_rna004 = "RNA004" in kit.upper() or "RNA004" in flow_cell.upper()
                return {"flow_cell": flow_cell, "kit": kit, "is_rna004": is_rna004}
    except Exception as e:
        print(f"[LocalPrereq] pod5 inspect failed (non-fatal): {e}")
    return {}


def _build_local_prereq_prompt(param_defs: list[dict], uploaded_files: list[str],
                                user_input: str, lang: str) -> str:
    required = [p for p in param_defs if p.get("required")]
    optional = [p for p in param_defs if not p.get("required")]
    files_str = "\n".join(f"  - {f}" for f in uploaded_files) or "  (none)"

    label_key = "label" if lang != "en_US" else "label_en"
    hint_key  = "hint"  if lang != "en_US" else "hint_en"

    def fmt_param(p: dict) -> str:
        label = p.get(label_key) or p.get("label", p["key"])
        hint  = p.get(hint_key)  or p.get("hint", "")
        dflt  = f'  default: "{p["default"]}"' if p.get("default") else ""
        opts  = (f'  MUST be one of: {p["options"]}' if p.get("type") == "select" and p.get("options") else "")
        return f'  "{p["key"]}": {label}\n    {hint}{dflt}{opts}'

    req_block  = "\n".join(fmt_param(p) for p in required)
    opt_block  = "\n".join(fmt_param(p) for p in optional) or "  (none)"

    if lang == "en_US":
        return f"""You are a bioinformatics assistant filling in workflow prerequisite parameters.

[Required parameters — must not be empty]
{req_block}

[Optional parameters — use default or empty string if not specified]
{opt_block}

[Uploaded files (use full absolute paths)]
{files_str}

[User request]
{user_input}

Rules:
- For required params: find the best matching file from the uploaded list using the full absolute path.
  If no matching file exists, set the value to null (not an empty string).
- For optional params: fill from user request; if absent use the default or empty string "".
- Output JSON only — no markdown, no code fences.

Return:
{{
  {', '.join(f'"{p["key"]}": "..."' for p in param_defs)}
}}
"""
    return f"""你是一个生物信息学助手，请根据用户上传的文件和需求，填写以下工作流前置参数。

【必填参数 — 不能为空】
{req_block}

【选填参数 — 未指定则用默认值或空字符串】
{opt_block}

【用户已上传的文件（使用完整绝对路径）】
{files_str}

【用户需求】
{user_input}

规则：
- 必填参数：从上传文件列表中找到最匹配的文件，使用完整绝对路径。
  如果没有匹配文件，设为 null（不是空字符串）。
- 选填参数：从用户需求中提取；如未指定则使用默认值或空字符串 ""。
- 只输出 JSON，不加 markdown 或代码块。

返回：
{{
  {', '.join(f'"{p["key"]}": "..."' for p in param_defs)}
}}
"""


def _extract_paths_from_input(user_input: str) -> list[str]:
    """Extract existing absolute paths mentioned directly in user input.
    Handles trailing sentence punctuation (e.g. '/ref.fa.Enable' → '/ref.fa').
    """
    import re
    raw = re.findall(r'(?<!\w)/[^\s\'"<>,;]+', user_input)
    result: list[str] = []
    seen: set[str] = set()
    for p in raw:
        if os.path.exists(p):
            if p not in seen:
                result.append(p)
                seen.add(p)
        else:
            # Strip trailing word appended by sentence punctuation, e.g. ".Enable"
            trimmed = re.sub(r'\.[A-Z][^./]*$', '', p)
            if trimmed != p and trimmed not in seen and os.path.exists(trimmed):
                result.append(trimmed)
                seen.add(trimmed)
    return result


def generate_local_prereqs_node(state: AgentState) -> dict:
    """
    For local workflows with local_params prereqs:
    1. LLM fills param values from uploaded files + user input.
    2. Optionally inspects pod5 kit metadata (non-fatal).
    3. Conditionally removes optional steps (e.g. modkit_pileup if no reference).
    4. Stores result in state["local_prereq_params"].
    """
    from utils.workflow_prerequisites import get_local_prereq_params
    import json
    import re

    selected_workflow = state.get("selected_workflow", "")
    param_defs = get_local_prereq_params(selected_workflow)
    if not param_defs:
        return {}

    user_input = state.get("input", "")
    uploaded_files = _list_session_files()
    for p in _extract_paths_from_input(user_input):
        if p not in uploaded_files:
            uploaded_files.append(p)
            print(f"[LocalPrereq] Added path from user input: {p}")
    lang = get_lang()
    llm = get_llm_instance(is_planner=True)

    prompt = _build_local_prereq_prompt(param_defs, uploaded_files, user_input, lang)

    ui_print("[LocalPrereq] Extracting workflow parameters via LLM...")
    MAX_RETRIES = 2
    params: dict = {}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = llm.invoke(prompt)
            content = raw if isinstance(raw, str) else raw.content
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            params = json.loads(content)
            break
        except Exception as e:
            ui_print(f"[LocalPrereq] Attempt {attempt} failed: {e}")

    if not params:
        # fallback: empty dict so user can fill manually
        params = {p["key"]: p.get("default", "") for p in param_defs}

    # ── Merge with preserved params: fill empty fields from previous run ──────
    # This ensures reference / data_file paths survive a re-run when the user's
    # new message doesn't mention them again, while still letting LLM override
    # when the user explicitly provides new values.
    preserved = state.get("local_prereq_params") or {}
    for p_def in param_defs:
        key = p_def["key"]
        if not params.get(key) and preserved.get(key):
            params[key] = preserved[key]

    # ── Normalise select-type params to canonical option values ──────────────
    # Guard against LLM choosing close-but-wrong values (e.g. "5mCpG" → "5mCG")
    for p_def in param_defs:
        if p_def.get("type") != "select":
            continue
        key   = p_def["key"]
        val   = (params.get(key) or "").strip()
        opts  = p_def.get("options", [])
        if val in opts:
            continue   # exact match — already canonical
        # Try case-insensitive match first
        val_lo = val.lower()
        matched = next((o for o in opts if o.lower() == val_lo), None)
        if matched:
            params[key] = matched
            continue
        # modification_type aliases: 5mCpG / 5mCG / CpG → "5mCG_5hmCG"
        if key == "modification_type":
            norm = val_lo.replace("-", "").replace("_", "").replace(" ", "")
            if norm in ("5mcpg", "5mcg", "cpg", "5hmcg", "5mcg5hmcg", "cpgmethylation"):
                params[key] = "5mCG_5hmCG"
            elif norm in ("5mc", "5hmc", "5mc5hmc"):
                params[key] = "5mC_5hmC"
        # else: keep LLM value; resolve_models has its own normalisation

    # ── pod5 kit inspection (non-fatal) ──────────────────────────────────────
    kit_info: dict = {}
    data_file = params.get("data_file") or ""
    if data_file and os.path.isfile(data_file) and data_file.endswith(".pod5"):
        kit_info = _inspect_pod5_kit(data_file)
        if kit_info:
            params["_kit_check"] = kit_info
            if kit_info.get("is_rna004") is False:
                params["_kit_warning"] = (
                    f"检测到 kit={kit_info.get('kit')}，非 RNA004，"
                    "请确认数据适合 RNA 修饰分析。"
                    if lang != "en_US" else
                    f"Detected kit={kit_info.get('kit')}, not RNA004. "
                    "Please confirm data is suitable for RNA modification analysis."
                )
            print(f"[LocalPrereq] kit check: {kit_info}")

    # ── conditional step removal ──────────────────────────────────────────────
    # If no reference → remove modkit_pileup from tool_sequence
    reference = params.get("reference") or ""
    tool_sequence = list(state.get("tool_sequence", []))
    if not reference:
        for step in ("samtools_faidx", "modkit_pileup"):
            if step in tool_sequence:
                tool_sequence.remove(step)
        print("[LocalPrereq] No reference provided — samtools_faidx and modkit_pileup removed from steps.")

    params["_workflow"] = selected_workflow   # tag for cross-run validation
    ui_print(f"[LocalPrereq] Parameters extracted: {list(k for k in params if not k.startswith('_'))}")
    return {
        "local_prereq_params": params,
        "tool_sequence": tool_sequence,
    }


def human_local_prereq_reviewer_node(state: AgentState) -> dict:
    """
    Interrupt node: pauses before execution so the UI can display local_prereq_params
    as an editable form. The UI writes confirmed values back via app.update_state()
    then resumes. This node validates required fields and warns on issues.
    """
    from utils.workflow_prerequisites import get_local_prereq_params
    from utils.ui_logger import ui_print

    selected_workflow = state.get("selected_workflow", "")
    param_defs = get_local_prereq_params(selected_workflow)
    params = state.get("local_prereq_params", {})

    missing = [
        p["key"] for p in param_defs
        if p.get("required") and not params.get(p["key"])
    ]
    if missing and not _skip_validation():
        ui_print(f"[LocalPrereq] WARNING — required params still missing: {missing}. "
                 "Please fill them in before proceeding.")

    kit_warning = params.get("_kit_warning", "")
    if kit_warning and not _skip_validation():
        ui_print(f"[LocalPrereq] ⚠ {kit_warning}")

    return {}
