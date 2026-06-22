def build_prereq_prompt(prereq: dict, uploaded_files: list[str], user_input: str,
                        lang: str = "zh_CN") -> str:
    columns = prereq["columns"]
    header = ",".join(columns)
    example = prereq["example_row"]
    description = prereq["description"]

    if lang == "en_US":
        files_str = "\n".join(f"  - {f}" for f in uploaded_files) if uploaded_files else "  (no uploaded files)"
        return f"""You are a bioinformatics expert. Generate a CSV samplesheet based on the uploaded files and user request.

[Samplesheet format]
{description}

Header (first line, fixed):
{header}

Example row:
{example}

[Uploaded files — use FULL absolute paths from this list]
{files_str}

[User request]
{user_input}

Output requirements:
- CRITICAL: Match filenames mentioned in the user request EXACTLY to the uploaded files list
  - If user says "analyze merged_1.pod5", use the file from the list that contains "merged_1" (or the exact filename)
  - ONLY include samples/files that the user explicitly mentioned or requested
  - Do NOT add extra files that the user did not request
- First line: the fixed header {header}
- Each data row represents one sample (only samples the user requested)
- For path/ref columns: copy the full absolute path exactly from the list above
- Leave empty string for columns that do not apply to that sample
- Output CSV plain text ONLY — no markdown, no code blocks, no explanations
- group/sample columns: if the user did not specify names, auto-generate group as 'group1','group2'... 
  and sample as the requested filename stem (without extension)
"""
    else:
        files_str = "\n".join(f"  - {f}" for f in uploaded_files) if uploaded_files else "  （无已上传文件）"
        return f"""你是生物信息学专家，需要根据用户上传的文件生成一个 CSV 格式的 samplesheet。

【samplesheet 格式说明】
{description}

表头（第一行，固定不变）：
{header}

示例行：
{example}

【用户已上传的文件（含完整绝对路径，直接填入 samplesheet，不要修改路径）】
{files_str}

【用户原始需求】
{user_input}

请根据上述文件列表和用户需求，生成完整的 samplesheet CSV 内容。
要求：
- 第一行必须是固定表头：{header}
- 每个数据行对应一个样本
- path/ref/fastq 等路径列必须使用上方文件列表中的完整绝对路径，不要截断目录
- 如果某列在该样本中不适用，填空字符串
- 只输出 CSV 纯文本，不要加任何说明、代码块标记或 <think> 标签
- group/sample 列：如果用户未指定，group 自动填写为 group1、group2...，
  sample 自动使用输入文件名去掉扩展名（如 PAU05248_pass_ffa693eb）
"""


def build_workflow_planner_prompt(lang: str = "en_US") -> str:
    """
    LLM prompt for workflow selection.
    Template variables: {input}, {history}, {workflow_list}
    {workflow_list} is built at call time from the registry — do not hard-code pipelines here.
    """
    if lang == "en_US":
        return """You are a bioinformatics workflow selection expert.

[Available Workflows]
{workflow_list}

[Hard Constraints]
- Select ONLY from the list above. Do not invent workflow names.
- Set "confident": true ONLY when ALL of the following are met:
    1. The user explicitly names a specific pipeline (e.g. "methylong", "nf-core/rnaseq")
    OR provides enough specifics (platform + molecule + input format) to uniquely identify one workflow
    2. No other workflow in the list could reasonably satisfy the request
  Otherwise set "confident": false and leave "workflow": null.
- Vague requests like "analyze methylation", "process long-read data", or "run methylation pipeline"
  MUST be treated as ambiguous (confident: false) because multiple workflows could apply.
- "candidates" must ALWAYS list every plausible option with a reason and recommended flag.
- Platform routing rules (set confident: true when platform is clear):
    * PacBio / HiFi / pb input → methylong ONLY (local workflows do not support PacBio)
    * Fiber-seq / 6mA accessibility / nucleosome positioning → methylong ONLY

[User Request]
{input}

[History]
{history}

Return JSON only — no markdown, no code fences:
{{
    "workflow": "exact workflow name from the list, or null if ambiguous",
    "confident": true or false,
    "reason": "one-sentence rationale",
    "candidates": [
        {{
            "name": "workflow name",
            "display_name": "display name",
            "type": "nfcore or local",
            "reason": "why this is a candidate",
            "recommended": true or false
        }}
    ]
}}
"""
    return """你是生物信息学工作流选择专家。

【可用工作流】
{workflow_list}

【约束】
- 只能从以上列表中选择，严禁自造名称。
- 仅当以下条件同时满足时，才将 "confident" 设为 true：
    1. 用户明确点名了某个流水线（如 "methylong"、"nf-core/rnaseq"）
    或 提供了足够明确的信息（平台 + 分子类型 + 输入格式）能唯一确定一个工作流
    2. 列表中没有其他工作流能合理满足需求
  否则将 "confident" 设为 false，"workflow" 设为 null。
- 模糊请求（如"分析甲基化"、"处理长读数据"、"运行甲基化流水线"）必须视为不确定（confident: false），
  因为多个工作流都可能适用。
- "candidates" 必须列出所有可行选项，每项包含理由和 recommended 标志。
- 平台路由规则（平台明确时直接设 confident: true）：
    * PacBio / HiFi / pb 数据 → 只能选 methylong（本地工作流不支持 PacBio）
    * Fiber-seq / 6mA 可及性 / 核小体定位 → 只能选 methylong

【用户需求】
{input}

【历史】
{history}

只返回 JSON，不加 markdown 或代码块：
{{
    "workflow": "列表中的工作流名称，不确定则为 null",
    "confident": true 或 false,
    "reason": "一句话说明选择理由",
    "candidates": [
        {{
            "name": "工作流名称",
            "display_name": "展示名称",
            "type": "nfcore 或 local",
            "reason": "为何推荐此选项",
            "recommended": true 或 false
        }}
    ]
}}
"""
