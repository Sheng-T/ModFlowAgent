"""
前置文件生成节点。

对于需要 samplesheet 等前置文件的 workflow，用 LLM 根据用户上传文件
自动生成文件内容，存入 state["pre_files"]，供审查和执行使用。
"""
import os

from agent_graph.state import AgentState
from agent_graph.prompts.workflow_prompts import build_prereq_prompt
from utils.workflow_prerequisites import get_prereqs
from utils.llm_utils import get_llm_instance
from utils.lang_utils import get_lang
from utils.user_context import get_session_dir


def _list_session_files(session_dir: str) -> list[str]:
    """Return full absolute paths of all files in session_dir (no subdirectories)."""
    if not session_dir or not os.path.isdir(session_dir):
        return []
    return [
        e.path for e in os.scandir(session_dir)
        if e.is_file()
    ]



def generate_prereqs_node(state: AgentState) -> dict:
    selected_workflow = state.get("selected_workflow", "")
    prereqs = get_prereqs(selected_workflow)

    if not prereqs:
        # 该 pipeline 无前置文件需求，直接跳过
        return {}

    session_dir = get_session_dir()
    uploaded_files = _list_session_files(session_dir)
    user_input = state.get("input", "")
    lang = get_lang()
    llm = get_llm_instance(is_planner=True)

    import re
    import csv
    import io

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
        """
        Validate generated content against the prereq spec.
        Returns (ok, reason).  Dispatches on prereq["type"].
        """
        if not content:
            return False, "content is empty"

        file_type = prereq.get("type", "")

        if file_type == "csv":
            required_cols = prereq.get("columns", [])
            try:
                reader = csv.DictReader(io.StringIO(content))
                header = reader.fieldnames or []
                missing_cols = [c for c in required_cols if c not in header]
                if missing_cols:
                    return False, f"missing columns: {missing_cols} (got header: {header})"
                data_rows = [r for r in reader if any(v.strip() for v in r.values())]
                if not data_rows:
                    return False, "header present but no data rows"
                # Check every required column has a non-empty value in every data row
                for row_idx, row in enumerate(data_rows, 1):
                    empty_cols = [c for c in required_cols if not (row.get(c) or "").strip()]
                    if empty_cols:
                        return False, f"row {row_idx} has empty values for required columns: {empty_cols}"
            except Exception as exc:
                return False, f"CSV parse error: {exc}"
            return True, ""

        # 未知类型：只检查非空
        return True, ""

    pre_files = []
    for prereq in prereqs:
        filename = prereq["filename"]
        print(f"[PrereqGenerator] Generating {filename}...")
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
                print(f"[PrereqGenerator] {filename} validation failed (attempt {attempt}): {fail_reason}, retrying...")
                content = ""
            except Exception as e:
                print(f"[PrereqGenerator] Attempt {attempt} exception: {e}")
                content = ""

        if not content:
            print(f"[PrereqGenerator] ERROR: {filename} still invalid after {MAX_RETRIES} attempts: {fail_reason}, skipping")
            continue

        pre_files.append({"filename": filename, "content": content})

    return {"pre_files": pre_files}


def human_prereq_reviewer_node(state: AgentState) -> dict:  # noqa: ARG001
    """
    Pass-through interrupt node between prereq_generator and param_generator.
    The graph pauses BEFORE this node so the UI can render an editable samplesheet.
    The UI calls app.update_state({"pre_files": edited}) then resumes — this node
    just forwards state unchanged.
    """
    _ = state  # intentionally unused; graph state is passed through unchanged
    return {}
