def build_qa_prompt(user_input: str, augmented_context: str, lang: str) -> str:
    """Build the Q&A prompt in the appropriate language."""
    if lang == "en_US":
        if augmented_context:
            return (
                "You are an expert bioinformatics assistant.\n\n"
                "The following reference material was retrieved to help answer the question. "
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
            "You are an expert bioinformatics assistant.\n\n"
            f"[Question]\n{user_input}\n\n"
            "Requirements:\n"
            "- Reply in English.\n"
            "- Use Markdown formatting (headings, bold, bullet lists where appropriate).\n"
            "- Keep the answer concise: under 400 words.\n"
            "- Be direct — lead with the answer, skip preamble."
        )
    else:
        if augmented_context:
            return (
                "你是生物信息学领域的专家助手。\n\n"
                "以下参考资料仅供参考，若与问题直接相关可适当引用，"
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
            "你是生物信息学领域的专家助手。\n\n"
            f"【用户问题】\n{user_input}\n\n"
            "回答要求：\n"
            "- 使用 Markdown 格式（适当使用标题、加粗、列表）。\n"
            "- 控制在 600 字以内，简洁直接。\n"
            "- 直接给出答案，不要写开场白。"
        )
