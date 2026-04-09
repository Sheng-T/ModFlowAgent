"""
前置文件生成节点。

对于需要 samplesheet 等前置文件的 workflow，用 LLM 根据用户上传文件
自动生成文件内容，存入 state["pre_files"]，供审查和执行使用。
"""
import os

from agent_graph.state import AgentState
from utils.workflow_prerequisites import get_prereqs
from utils.llm_utils import get_llm_instance
from utils.user_context import get_session_dir


def _list_session_files(session_dir: str) -> list[str]:
    """列出 session_dir 下的所有文件名（不含子目录）。"""
    if not session_dir or not os.path.isdir(session_dir):
        return []
    return [
        e.name for e in os.scandir(session_dir)
        if e.is_file()
    ]


def _build_prompt(prereq: dict, uploaded_files: list[str], user_input: str) -> str:
    columns = prereq["columns"]
    header = ",".join(columns)
    example = prereq["example_row"]
    description = prereq["description"]

    files_str = "\n".join(f"  - {f}" for f in uploaded_files) if uploaded_files else "  （无已上传文件）"

    return f"""你是生物信息学专家，需要根据用户上传的文件生成一个 CSV 格式的 samplesheet。

【samplesheet 格式说明】
{description}

表头（第一行，固定不变）：
{header}

示例行：
{example}

【用户已上传的文件】
{files_str}

【用户原始需求】
{user_input}

请根据上述文件列表和用户需求，生成完整的 samplesheet CSV 内容。
要求：
- 第一行必须是固定表头：{header}
- 每个数据行对应一个样本，路径只填文件名（不含目录前缀）
- 如果某列在该样本中不适用，填空字符串
- 只输出 CSV 纯文本，不要加任何说明或代码块标记
"""


def generate_prereqs_node(state: AgentState) -> dict:
    selected_workflow = state.get("selected_workflow", "")
    prereqs = get_prereqs(selected_workflow)

    if not prereqs:
        # 该 pipeline 无前置文件需求，直接跳过
        return {}

    session_dir = get_session_dir()
    uploaded_files = _list_session_files(session_dir)
    user_input = state.get("input", "")
    llm = get_llm_instance(is_planner=False)

    pre_files = []
    for prereq in prereqs:
        print(f"[PrereqGenerator] 正在生成 {prereq['filename']} ...")
        prompt = _build_prompt(prereq, uploaded_files, user_input)
        try:
            import re
            raw = llm.invoke(prompt)
            content = raw if isinstance(raw, str) else raw.content
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1]
                content = content.rsplit("```", 1)[0].strip()
            pre_files.append({
                "filename": prereq["filename"],
                "content": content,
            })
            print(f"[PrereqGenerator] {prereq['filename']} 生成完成")
        except Exception as e:
            print(f"[PrereqGenerator] 生成 {prereq['filename']} 失败: {e}")

    return {"pre_files": pre_files}
