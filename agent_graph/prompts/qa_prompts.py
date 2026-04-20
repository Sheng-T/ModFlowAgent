def build_platform_context() -> str:
    """
    Build a compact description of all tools and pipelines available on this platform.
    Called once per Q&A invocation so it always reflects the current config.
    """
    from configs.tool_config import TOOL_DESCRIPTION
    from configs.workflow_config import PIPELINE_DESCRIPTIONS

    lines = ["## Available tools on this platform"]
    for t in TOOL_DESCRIPTION:
        if t["name"] == "workflow":
            continue
        lines.append(f"- **{t['name']}**: {t['description']}")

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


def build_qa_prompt(user_input: str, augmented_context: str, lang: str,
                    platform_context: str = "") -> str:
    """Build the Q&A prompt in the appropriate language."""
    platform_block_en = (
        f"\n[Platform context — tools and pipelines available on this system]\n{platform_context}\n"
        if platform_context else ""
    )
    platform_block_zh = (
        f"\n【平台工具信息 — 本系统可用的工具与流水线】\n{platform_context}\n"
        if platform_context else ""
    )

    if lang == "en_US":
        if augmented_context:
            return (
                "You are an expert bioinformatics assistant for a nanopore sequencing analysis platform.\n"
                "When the user asks about tools or pipelines, answer based on what is actually available "
                "on this platform (listed below). Do not invent tools or capabilities not listed.\n"
                f"{platform_block_en}"
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
            "When the user asks about tools or pipelines, answer based on what is actually available "
            "on this platform (listed below). Do not invent tools or capabilities not listed.\n"
            f"{platform_block_en}"
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
                "当用户询问工具或流水线时，请根据本平台实际可用的工具作答（见下方列表），不要编造未列出的工具或功能。\n"
                f"{platform_block_zh}"
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
            "当用户询问工具或流水线时，请根据本平台实际可用的工具作答（见下方列表），不要编造未列出的工具或功能。\n"
            f"{platform_block_zh}"
            f"\n【用户问题】\n{user_input}\n\n"
            "回答要求：\n"
            "- 使用 Markdown 格式（适当使用标题、加粗、列表）。\n"
            "- 控制在 600 字以内，简洁直接。\n"
            "- 直接给出答案，不要写开场白。"
        )
