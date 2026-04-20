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
    if lang == "en_US":
        return """
    You are a bioinformatics workflow selection expert.

    [Hard Constraints]:
    - Select exactly one pipeline
    - The pipeline name must come strictly from the [Supported Pipelines] list — do not invent names
    - Return only the pipeline name, no parameters

    [Supported Pipelines]:
    - methylong: Long-read methylation analysis for ONT or PacBio HiFi; input: BAM + reference genome FASTA

    [Pipeline Documentation]:
    {workflow_context}

    User request:
    {input}

    History:
    {history}

    Return JSON only:
    {{
        "pipeline": "pipeline name, must be methylong",
        "reason": "one-sentence rationale"
    }}
    """
    return """
    你是一个生物信息学 workflow 选择专家。

    【强约束】：
    - 只能选择一个 pipeline
    - pipeline 名称必须严格来自【当前支持的 Pipeline】列表，严禁自造或使用列表之外的名称
    - 不要返回参数，只返回 pipeline 名称

    【当前支持的 Pipeline】:
    - methylong：ONT 或 PacBio HiFi 长读长甲基化分析，输入 BAM + 参考基因组 FASTA

    【Pipeline 文档参考】:
    {workflow_context}

    用户需求:
    {input}

    历史:
    {history}

    请返回 JSON:
    {{
        "pipeline": "pipeline名称，只能是 methylong",
        "reason": "选择理由，一句话"
    }}
    """
