import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SingleToolRule:
    tool_name: str
    keywords: tuple[str, ...]


SINGLE_TOOL_RULES: tuple[SingleToolRule, ...] = (
    SingleToolRule("fastqc", ("fastqc", "fastq", ".fastq", ".fq", "fq.gz", "fastq.gz")),
    SingleToolRule("dorado", ("dorado", "basecall")),
    SingleToolRule("samtools", ("samtools", "sort", "index")),
    SingleToolRule("modkit", ("modkit",)),
)


def resolve_single_tool_request(user_input: str) -> str | None:
    lower = (user_input or "").lower()
    for rule in SINGLE_TOOL_RULES:
        if any(keyword in lower for keyword in rule.keywords):
            return rule.tool_name
    return None


def fallback_single_tool_candidates(user_input: str) -> list[str]:
    lower = (user_input or "").lower()
    matches: list[str] = []
    for rule in SINGLE_TOOL_RULES:
        if any(keyword in lower for keyword in rule.keywords):
            matches.append(rule.tool_name)
    return list(dict.fromkeys(matches))


def _output_location(run_dir: str, lang: str) -> str:
    if not run_dir:
        return ""
    if lang == "en_US":
        return f"\n\nServer output directory: `{run_dir}`"
    return f"\n\n服务器输出目录：`{run_dir}`"


def format_single_tool_raw_output(tool_output: list, run_dir: str, lang: str) -> str:
    raw_lines = "\n".join(
        line for line in tool_output if str(line).strip().lower() != "null"
    ).strip()
    if raw_lines:
        prefix = "**Command output:**\n\n" if lang == "en_US" else "**命令输出：**\n\n"
        answer = prefix + "```\n" + raw_lines + "\n```"
    else:
        answer = (
            "Command completed with no output."
            if lang == "en_US"
            else "命令执行完成，无可展示的标准输出。"
        )
    return answer + _output_location(run_dir, lang)


def summarize_single_tool_outputs(
    tool_calls: list[dict],
    tool_output: list,
    existing_output_paths: list[str],
    run_dir: str,
    llm,
    lang: str,
) -> str:
    rel_outputs = []
    for path in existing_output_paths[:20]:
        try:
            rel_outputs.append(os.path.relpath(path, run_dir) if run_dir else path)
        except Exception:
            rel_outputs.append(path)
    output_list_md = "\n".join(f"- `{p}`" for p in rel_outputs)
    output_location = _output_location(run_dir, lang)
    tool_names = [str(c.get("tool_name", "")).lower() for c in tool_calls]

    if tool_names == ["fastqc"]:
        raw_output_text = "\n".join(
            line for line in tool_output if str(line).strip().lower() != "null"
        ).strip()[:1200]
        prompt = f"""You are a bioinformatics assistant. A FastQC run completed successfully.

[Raw execution summary]
{raw_output_text}

[Generated files]
{output_list_md}

[Server output directory]
{run_dir or "(not available)"}

Write a short Markdown result note for the user.
Requirements:
1. State that FastQC completed successfully.
2. Explain that the HTML report is the main file to open and the ZIP file contains the raw module data.
3. Mention that detailed QC interpretation still requires reading the FastQC report itself.
4. Tell the user where the server-side result directory is located.
5. Keep it concise and practical. Do not invent QC findings that were not provided."""
        try:
            raw_report = llm.invoke(prompt)
            report = raw_report if isinstance(raw_report, str) else raw_report.content
            report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
            return report + output_location
        except Exception:
            if lang == "en_US":
                answer = (
                    "### FastQC completed\n\n"
                    "FastQC finished successfully. Open the HTML report below for the main QC summary, "
                    "and use the ZIP file if you need the raw module outputs.\n\n"
                    f"{output_list_md}"
                )
            else:
                answer = (
                    "### FastQC 已完成\n\n"
                    "FastQC 已成功运行。请优先打开下方 HTML 报告查看主要质控结果，"
                    "ZIP 文件则包含原始模块输出。\n\n"
                    f"{output_list_md}"
                )
            return answer + output_location

    if lang == "en_US":
        answer = (
            "### Command completed\n\n"
            "The tool finished successfully and generated the following output files:\n\n"
            f"{output_list_md}"
        )
    else:
        answer = (
            "### 命令执行完成\n\n"
            "工具已成功运行，并生成了以下输出文件：\n\n"
            f"{output_list_md}"
        )
    return answer + output_location
