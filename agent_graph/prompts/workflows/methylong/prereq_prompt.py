"""
methylong-specific samplesheet generation prompt.
Loaded dynamically by generate_prereqs_node when selected_workflow == "methylong".
"""


def build_prereq_prompt(prereq: dict, uploaded_files: list[str], user_input: str,
                        lang: str = "en_US", feedback: str = "") -> str:
    columns = prereq["columns"]
    header = ",".join(columns)
    example = prereq["example_row"]
    description = prereq["description"]

    method_rule = (
        "- method column rules (only 'ont' or 'pacbio' are valid):\n"
        "    * 'ont'    — Oxford Nanopore; DEFAULT when platform is not stated\n"
        "    * 'pacbio' — PacBio HiFi; only when user explicitly says \"PacBio\", \"HiFi\", or \"pb\"\n"
        "  DO NOT infer method from the filename."
    )
    method_rule_zh = (
        "- method 列只有两个合法值：'ont' 或 'pacbio'：\n"
        "    * 'ont'    — 牛津纳米孔；未指定平台时默认填此值\n"
        "    * 'pacbio' — PacBio HiFi；仅当用户明确说 \"PacBio\"、\"HiFi\" 或 \"pb\" 时才填\n"
        "  不要从文件名推断 method。"
    )

    if lang == "en_US":
        files_str = "\n".join(f"  - {f}" for f in uploaded_files) if uploaded_files else "  (no uploaded files)"
        feedback_block = f"\n[User correction]\n{feedback}\nPlease fix the samplesheet based on the above correction.\n" if feedback else ""

        return f"""You are a bioinformatics expert. Generate a CSV samplesheet based on the uploaded files and user request.{feedback_block}

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

Rules:
- Line 1 MUST be the literal header: {header}
- Lines 2+ are data rows, one sample per row
- File selection rules:
  * If the user explicitly names specific files: include only those files (match by filename or stem)
  * If the user's request is general (no specific files named): include ALL relevant uploaded files
    (BAM, pod5, fast5 files are relevant; ignore unrelated files like text/log files)
  * If NO files were uploaded at all: generate placeholder row(s) based on what the user mentioned:
      - ONT data mentioned (or no platform specified): path=/path/to/sample.pod5, ref=/path/to/ref.fa, method=ont
      - PacBio data mentioned: path=/path/to/sample.bam, ref=/path/to/ref.fa, method=pacbio
      - Both ONT and PacBio mentioned: generate TWO rows, one for each platform
    so the user can edit them — do NOT leave the samplesheet empty
- For path/ref columns: copy the full absolute path exactly from the uploaded files list above
- ref column rules:
    * If the user explicitly provides a reference path, use it
    * If the user does NOT mention a reference, scan the uploaded files list for any file ending in
      .fa, .fasta, or .fna and use that as ref (same ref for all rows)
    * Only leave ref empty if no reference file exists in the uploaded files list
- Leave empty string for columns that do not apply to that sample
- Output CSV plain text ONLY — no markdown fences, no code blocks, no explanations, no blank lines before the header
- group/sample columns:
  * group: if the user did not specify group names —
    - use 'group1' for ALL rows when samples should be analyzed "together", "jointly",
      or belong to the same condition/experiment
    - otherwise auto-generate 'group1', 'group2'... (one per row)
  * sample: always use the filename stem (without extension); use 'sample' for placeholder rows
{method_rule}
"""
    else:
        files_str = "\n".join(f"  - {f}" for f in uploaded_files) if uploaded_files else "  （无已上传文件）"
        feedback_block = f"\n【用户纠错】\n{feedback}\n请根据上述纠错重新生成 samplesheet。\n" if feedback else ""

        return f"""你是生物信息学专家，需要根据用户上传的文件生成一个 CSV 格式的 samplesheet。{feedback_block}

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

要求：
- 第 1 行必须是字面表头：{header}
- 第 2 行起为数据行，每个样本占一行
- 文件选取规则：
    * 用户明确提及具体文件名时：只包含这些文件（按文件名或去扩展名匹配）
    * 用户需求较笼统（未点名具体文件）：把上传列表中所有相关文件都加入
      （BAM、pod5、fast5 属于相关文件；文本/日志等无关文件忽略）
    * 若完全没有上传文件：根据用户提及的平台生成占位符行：
        - 提及 ONT 或未指定平台：path=/path/to/sample.pod5, ref=/path/to/ref.fa, method=ont
        - 提及 PacBio：path=/path/to/sample.bam, ref=/path/to/ref.fa, method=pacbio
        - 同时提及 ONT 和 PacBio：生成两行，各平台一行
      方便用户手动修改——不允许只输出表头、没有任何数据行
- path/ref 等路径列必须使用上方文件列表中的完整绝对路径
- ref 列规则：
    * 用户明确提供参考基因组路径时直接使用
    * 用户未提及参考基因组时，扫描上传文件列表，找到以 .fa、.fasta 或 .fna 结尾的文件用作 ref
    * 仅当上传文件中确实没有参考基因组文件时才将 ref 留空
- 如果某列在该样本中不适用，填空字符串
- 只输出 CSV 纯文本，不要加任何说明、代码块标记或 <think> 标签，表头前不要有空行
- group/sample 列：
  * group：用户未指定时——
    - 用户说"一起"、"同时分析"、"同一批/组/条件"时，所有行统一填 'group1'
    - 否则按行自动递增：group1、group2...
  * sample：始终使用输入文件名去掉扩展名；占位符行用 'sample'
{method_rule_zh}
"""
