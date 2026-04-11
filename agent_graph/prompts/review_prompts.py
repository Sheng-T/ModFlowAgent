def build_human_review_feedback_prompt(
    user_input: str, tool_calls, identified_tools, lang: str = "en_US"
) -> str:
    if lang == "en_US":
        return f"""
        User feedback: {user_input}
        Currently planned steps: {tool_calls}
        Currently selected tools: {identified_tools}

        Evaluate the scope of this feedback and return strictly one of the following three words:
        - 'SELECTOR': The user wants to introduce a completely new software category (e.g. originally only dorado, now requesting samtools). Return if the newly requested tool is not among the selected tools.
        - 'REPLAN': Involves adding or removing logical steps within the same software (e.g. add a samtools index step after samtools sort). Return if the newly requested tool is already among the selected tools.
        - 'REPARAM': Only modifying parameters of existing steps (e.g. changing input/output paths, model version, adding --reference). No new steps added.

        Return exactly one word, no other characters.
        """
    return f"""
        用户反馈: {user_input}
        当前已规划的步骤: {tool_calls}
        当前选取的工具: {identified_tools}

        请评估该反馈的影响范围，严格返回以下三个单词之一:
        - 'SELECTOR': 用户要求引入全新的软件大类（例如：原来只有dorado，现在要求使用samtools进行处理），如果用户新选取的工具不在已选工具中返回。
        - 'REPLAN': 涉及同一软件的逻辑步骤增减（例如：要求在原有的samtools sort之后，再加一步samtools index），如果用户新选取的工具在已选工具中返回。
        - 'REPARAM': 仅仅修改已有步骤的参数内容（例如：修改输入输出路径、修改模型版本、添加--reference文件），不增加任何新步骤。

        只返回一个单词，不要有任何其他字符。
        """
