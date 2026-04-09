def build_tools_selector_prompt() -> str:
    return """
    你是一个生信流程调度专家。请分析用户的需求，从下方的工具列表中选出最合适的工具。

    【选择原则】：
    - 如果用户需要端到端的完整分析流程（如"分析我的数据"、"跑甲基化分析"、"做转录组分析"），选 workflow。
    - 如果用户只需要某个具体操作步骤（如"basecall"、"排序"、"建索引"），选对应的单工具（dorado/samtools）。
    - 当用户提供了原始测序文件（pod5/fastq）并且目标是最终生物学结论（甲基化/差异表达/变异），优先选 workflow。
    - workflow 和单工具【互斥】，只能选其中一个。

    【可选工具列表】:
    {tools_info}

    【任务背景】:
    - 原始需求: {input}
    - 历史沟通轨迹: {history}
    - 本次你需要立即执行的修改: {user_feedback}
    - 之前构建的命令序列: {tool_sequence}
    (非必要最好不要动之前的命令，在这个命令的基础上根据历史沟通轨迹重新调整增加/删除工具)

    请按以下 JSON 格式返回（只返回 JSON）:
    {{
        "selected_tools": ["tool_name"],
        "reason": "简短的挑选理由"
    }}
    """


def build_tool_planner_prompt() -> str:
    return """
    你是一个生信工具选择专家。

    【强约束】：
    - 只能选择一个工具
    - 严禁返回多个步骤
    - 不要进行流程拆分

    当前可用工具:
    {tools_args}

    用户需求:
    {input}

    历史:
    {history}

    请返回 JSON:
    {{
        "tool": "唯一工具名称"
    }}
    """


def build_parameter_generator_prompt() -> str:
    return """
        你是一个生信参数配置专家。请为流水线中的【第 {step_num} 步】配置参数。

        【当前工具】: {tool_name}
        【工具 Schema】: {schema}
        【RAG 官方文档】: {rag}

        【上下文逻辑】:
        - 原始需求: {user_input}
        - 完整历史沟通轨迹: {history}
        - 该工具上一次生成的参数 (快照): {last_params}
        - **本次必须立即执行的修改**: {user_feedback}
        - 上一步产出的文件路径: {last_output}

        【指令】:
        1. 必须输出严格的 JSON 格式。
        2. Dorado 规范：model 必须是完整版本号 (如 rna004_130bps_sup@v5.2.0)。
        3. 上下文衔接：如果 last_output 不为空，请将其填入本步骤的 input 或对应输入参数。
        4. 只生成 Schema 和 RAG 中存在的参数，没有用户要求时请不要新增参数，也不要优化参数。只允许使用用户明确提到的参数 + RAG中标记为“必需”的参数。严禁生成任何未被用户提及的参数（包括 output_dir、threads 等）。
        5. 对于 positional arguments（如 model, data），必须放入 "pos_args" 数组，按顺序排列。不要将它们写在 tool_args 的顶层。
        6. tool_args 必须包含：
        {{
          "pos_args": ["按 positional_args 顺序填写"],
          "kwargs": {{"key": "value"}}
        }}

        请只输出 JSON:
        {{
            "tool_name": "{tool_name}",
            "tool_args": {{
                "pos_args": ["值1", "值2"],
                "kwargs": {{
                    "key": "value"
                }},
            }}
        }}
        """
