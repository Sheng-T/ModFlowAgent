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
