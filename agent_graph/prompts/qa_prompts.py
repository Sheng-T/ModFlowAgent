def build_platform_context() -> str:
    """
    Build a compact description of all tools and pipelines available on this platform.
    Called once per Q&A invocation so it always reflects the current config.
    """
    from configs.tool_config import TOOL_DESCRIPTION
    from configs.workflow_config import PIPELINE_DESCRIPTIONS, LOCAL_PIPELINE_DESCRIPTIONS

    lines = ["## Available tools on this platform"]
    for t in TOOL_DESCRIPTION:
        if t["name"] == "workflow":
            continue
        lines.append(f"- **{t['name']}**: {t['description']}")

    if LOCAL_PIPELINE_DESCRIPTIONS:
        lines.append("\n## Available local workflows (per-tool Singularity, no Nextflow required)")
        for p in LOCAL_PIPELINE_DESCRIPTIONS:
            lines.append(f"- **{p['name']}**: {p['description']} (input: {p['input']})")

    if PIPELINE_DESCRIPTIONS:
        lines.append("\n## Available end-to-end pipelines (Nextflow/nf-core)")
        for p in PIPELINE_DESCRIPTIONS:
            lines.append(f"- **{p['name']}**: {p['description']} ({p['input']})")

    return "\n".join(lines)


def build_search_decision_prompt(user_input: str) -> str:
    """Ask the LLM whether web search would meaningfully improve the answer."""
    return (
        "You are a routing assistant. Decide whether a web search is needed to answer the user's message.\n\n"
        "Answer YES only if the message is a specific technical question (e.g. about a tool, method, "
        "or biological concept) where up-to-date or detailed external information would clearly help.\n"
        "Answer NO for: greetings, small-talk, vague statements, simple factual questions the model "
        "already knows well, or anything unrelated to bioinformatics.\n\n"
        f"User message: {user_input}\n\n"
        "Reply with exactly one word: YES or NO."
    )


def _load_workflow_qa_hints(workflow: str, lang: str) -> str:
    """Dynamically load per-workflow QA hints, return empty string if unavailable."""
    if not workflow:
        return ""
    try:
        import importlib
        mod = importlib.import_module(f"agent_graph.prompts.workflows.{workflow}.qa_rules")
        if hasattr(mod, "get_qa_hints"):
            return mod.get_qa_hints(lang)
    except ModuleNotFoundError:
        pass
    return ""


def build_qa_prompt(user_input: str, augmented_context: str, lang: str,
                    platform_context: str = "", workflow_hints: str = "",
                    router_hint: str = "") -> str:
    """Build the Q&A prompt in the appropriate language."""
    platform_block_en = (
        f"\n[Platform context — tools and pipelines available on this system]\n{platform_context}\n"
        if platform_context else ""
    )
    platform_block_zh = (
        f"\n【平台工具信息 — 本系统可用的工具与流水线】\n{platform_context}\n"
        if platform_context else ""
    )
    hints_block_en = (
        f"\n[Pipeline-specific guidance — apply when relevant]\n{workflow_hints}\n"
        if workflow_hints else ""
    )
    hints_block_zh = (
        f"\n【流水线专项说明 — 相关时优先遵循】\n{workflow_hints}\n"
        if workflow_hints else ""
    )
    # router_hint is set when the router intercepted an unsupported combination;
    # inject it as a hard constraint so the LLM cannot suggest invalid workflows.
    router_hint_block_en = (
        f"\n[CRITICAL — unsupported combination detected]\n{router_hint}\n"
        f"Your answer MUST clearly state this is not supported and explain the correct alternative.\n"
        if router_hint else ""
    )
    router_hint_block_zh = (
        f"\n【严重警告 — 检测到不支持的组合】\n{router_hint}\n"
        f"你的回答必须明确说明此组合不受支持，并告知正确的替代方案。\n"
        if router_hint else ""
    )

    # Hard rule injected into every prompt to prevent the platform tool list from
    # being misread as a capability whitelist for general bioinformatics questions.
    no_whitelist_rule_en = (
        "IMPORTANT: NEVER say a tool is 'not supported on this platform' or 'not available here' "
        "unless the user explicitly asks whether THIS PLATFORM supports it. "
        "For any general bioinformatics question (e.g. comparing tools, asking about methods, "
        "'when to use X vs Y?'), answer purely from your bioinformatics expertise — "
        "the platform tool list above is context only, NOT a whitelist of allowed topics.\n"
    )
    no_whitelist_rule_zh = (
        "重要：除非用户明确询问本平台是否支持某工具，否则绝对不要说某工具【本平台不支持】或【不可用】。"
        "对于任何通用生信问题（例如工具对比、方法选择、'什么时候用X还是Y？'），"
        "请直接用你的专业知识作答——上方平台工具列表仅供背景参考，不是话题白名单。\n"
    )

    if lang == "en_US":
        if augmented_context:
            return (
                "You are an expert bioinformatics assistant for a nanopore sequencing analysis platform.\n"
                "Use your full bioinformatics expertise to answer any question about sequencing, methods, "
                "or biological concepts. Only when the user asks specifically what this platform CAN DO "
                "(e.g. 'does this system support X?', 'which tools are available?') should you restrict "
                "your answer to the tools listed below.\n"
                f"{platform_block_en}"
                f"{no_whitelist_rule_en}"
                f"{hints_block_en}"
                f"{router_hint_block_en}"
                "\nThe following reference material was retrieved to help answer the question. "
                "Use it only if it is clearly relevant — if it drifts off-topic or adds little value, "
                "ignore it entirely and answer from your own expertise. "
                "Never mention or evaluate the reference material in your answer.\n\n"
                f"[Reference]\n{augmented_context}\n\n"
                f"[Question]\n{user_input}\n\n"
                "Requirements:\n"
                "- Reply in English.\n"
                "- Use Markdown formatting (headings, bold, bullet lists where appropriate).\n"
                "- Keep the answer concise: under 400 words.\n"
                "- Be direct — lead with the answer, skip preamble."
            )
        return (
            "You are an expert bioinformatics assistant for a nanopore sequencing analysis platform.\n"
            "Use your full bioinformatics expertise to answer any question about sequencing, methods, "
            "or biological concepts. Only when the user asks specifically what this platform CAN DO "
            "(e.g. 'does this system support X?', 'which tools are available?') should you restrict "
            "your answer to the tools listed below.\n"
            f"{platform_block_en}"
            f"{no_whitelist_rule_en}"
            f"{hints_block_en}"
            f"{router_hint_block_en}"
            f"\n[Question]\n{user_input}\n\n"
            "Requirements:\n"
            "- Reply in English.\n"
            "- Use Markdown formatting (headings, bold, bullet lists where appropriate).\n"
            "- Keep the answer concise: under 400 words.\n"
            "- Be direct — lead with the answer, skip preamble."
        )
    else:
        if augmented_context:
            return (
                "你是一个纳米孔测序分析平台的生物信息学专家助手。\n"
                "对于测序技术、生物学概念、分析方法等通用生信问题，请直接用你的专业知识作答。\n"
                "只有当用户明确询问本平台的功能或能力（如【你们支持X吗】【有哪些工具】）时，"
                "才需要参照下方工具列表，不要编造未列出的工具或功能。\n"
                f"{platform_block_zh}"
                f"{no_whitelist_rule_zh}"
                f"{hints_block_zh}"
                f"{router_hint_block_zh}"
                "\n以下参考资料仅供参考，若与问题直接相关可适当引用，"
                "若关联不足或内容偏离，请完全忽略，直接用自己的专业知识回答。"
                "不要在答案中提及或评价参考资料本身。\n\n"
                f"【参考资料】\n{augmented_context}\n\n"
                f"【用户问题】\n{user_input}\n\n"
                "回答要求：\n"
                "- 使用 Markdown 格式（适当使用标题、加粗、列表）。\n"
                "- 控制在 600 字以内，简洁直接。\n"
                "- 直接给出答案，不要写开场白。"
            )
        return (
            "你是一个纳米孔测序分析平台的生物信息学专家助手。\n"
            "对于测序技术、生物学概念、分析方法等通用生信问题，请直接用你的专业知识作答。\n"
            "只有当用户明确询问本平台的功能或能力（如【你们支持X吗】【有哪些工具】）时，"
            "才需要参照下方工具列表，不要编造未列出的工具或功能。\n"
            f"{platform_block_zh}"
            f"{no_whitelist_rule_zh}"
            f"{hints_block_zh}"
            f"{router_hint_block_zh}"
            f"\n【用户问题】\n{user_input}\n\n"
            "回答要求：\n"
            "- 使用 Markdown 格式（适当使用标题、加粗、列表）。\n"
            "- 控制在 600 字以内，简洁直接。\n"
            "- 直接给出答案，不要写开场白。"
        )
