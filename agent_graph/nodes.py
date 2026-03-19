# 假设你的 LLM 已经通过 HuggingFacePipeline 实例化
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
# llm = HuggingFacePipeline(...)
import re
from typing import TypedDict
from agent_graph.state import AgentState, EMPTY_STATE
import os
import sys

from data_storage.rag_retriever import EnhancedMDRAG
from runtime.env_wrapper import EnvWrapper
from runtime.executor import ToolExecutor
from tools import tools_verify
from tools.tools_verify import build_shell_args

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_utils import get_llm_instance
from utils.nodes_utils import format_history

from utils.common_utils import TOOL_LIST, TOOLS_DOC, TOOL_ARGS, llm_args, \
    TOOL_DESCIPTION, AGENT_PATH, DATA_PATH
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import json
import torch

# 1. 意图路由/决策节点
# 节点函数本身现在只需要返回 state
# 保护记忆：intent_router 在重置时要继承历史
def intent_router(state: AgentState) -> AgentState:
    user_input = state["input"]
    print(f"\n[Router] 正在分析用户输入: '{user_input[:30]}...'")

    # 继承原始输入和对话历史，清空其他执行状态
    history = state.get("chat_history", [])
    return {**EMPTY_STATE, "input": user_input, "chat_history": history}

def router_selector(state: AgentState) -> str:
    user_input = state["input"].lower()

    # 1. 保留核心规则（保留效率）
    # if any(k in user_input for k in ["basecall", "修饰", "数据","executor","tool"]):
    #     return "route_to_rag"

    # 2. 降级逻辑：交给 LLM 做深度路由（提升智能）
    print("[Router] 规则未匹配，正在请求 LLM 进行意图分析...")
    llm = get_llm_instance(is_planner=True,temperature=0.2)

    classification = llm.invoke(
        f"你是一个生物信息学专家助手。请分析用户意图并分类：\n"
        f"- 如果用户要求执行具体的操作（如 basecall、排序、统计、运行工具），返回 'tools'；\n"
        f"- 如果用户是询问生物学概念、生信知识、技术原理（如纳米孔、DNA、测序），返回 'answer'；\n"
        f"- 只有当用户在闲聊、骂人或说与科学完全无关的话时，才返回 'irrelevant'。\n"
        f"注意：只返回单词本身，不要任何标点。\n"
        f"用户输入: {user_input}"
    )

    # 确保去掉所有可能产生的空格或换行
    clean_intent = (classification.strip().lower().replace("`", "")
                    .replace("json", "").replace("{", "").replace("}","").replace('"','').strip())

    # print(f'clean_intent {clean_intent}')
    mapping = {
        "tools": "tools",
        "tool": "tools",
        "llmanswer": "answer",
        "irrelevant": "irrelevant"
    }
    final_intent = mapping.get(clean_intent, "answer")

    return f"route_to_{final_intent}"


# ------------------------------------------------------------------------------

def tools_selector(state: AgentState) -> AgentState:
    """
    智能工具选择器：判断用户需求涉及哪些工具（如同时涉及 dorado 和 samtools）。
    """
    user_input = state["input"]
    user_feedback = state.get("user_feedback", "")
    history_str = format_history(state.get("chat_history", []))
    tool_sequence = state.get("tool_sequence", [])
    print(f"\n[Tools Selector] 正在分析任务涉及的工具...")

    # 1. 构造工具描述，让 LLM 了解每个工具能干什么
    tools_info = "\n".join([f"- {t['name']}: {t['description']}" for t in TOOL_DESCIPTION])

    # if user_feedback:
    #     user_input = f"初始需求: {user_input}\n用户最新追加/修改指令: {user_feedback}\n之前构建的命令: {tool_sequence}\n非必要最好不要动之前的命令，在这个命令的基础上重新调整增加/删除工具"

    # 2. 构造 Prompt
    prompt = ChatPromptTemplate.from_template("""
    你是一个生信流程调度专家。请分析用户的需求，从下方的工具列表中挑选出完成任务所需的【所有】工具。

    【可选工具列表】:
    {tools_info}

    任务背景】:
    - 原始需求: {input}
    - 历史沟通轨迹: {history}
    - 本次你需要立即执行的修改: {user_feedback}
    - 之前构建的命令序列: {tool_sequence}
    (非必要最好不要动之前的命令，在这个命令的基础上根据历史沟通轨迹重新调整增加/删除工具)

    请按以下 JSON 格式返回（只返回 JSON）:
    {{
        "selected_tools": ["tool_name1", "tool_name2"],
        "reason": "简短的挑选理由"
    }}
    """)

    # 3. 调用 LLM 进行判断
    selector_llm = get_llm_instance(is_planner=True)
    chain = prompt | selector_llm | JsonOutputParser()

    try:
        response = chain.invoke({
            "input": user_input,
            "tools_info": tools_info,
            "history": history_str,
            "tool_sequence": tool_sequence,
            "user_feedback": user_feedback
        })

        selected = response.get("selected_tools", [])

        # 4. 安全校验：过滤掉不在列表中的工具，并防止为空
        valid_tools = [t for t in selected if t in TOOLS_DOC.keys()]

        if not valid_tools:
            # 简单模糊匹配兜底（如果 LLM 没匹配出，通过关键字强制兜底）
            if "basecall" in user_input.lower() or "dorado" in user_input.lower():
                valid_tools.append("dorado")
            if "sort" in user_input.lower() or "index" in user_input.lower():
                valid_tools.append("samtools")

        # 5. 更新 State
        state["identified_tools"] = list(set(valid_tools))  # 去重
        print(f"[Tools Selector] 已确定工具链: {state['identified_tools']}")
        print(f"[Tools Selector] 理由: {response.get('reason', '无')}")

    except Exception as e:
        print(f"[Tools Selector Error] 解析失败，使用默认兜底: {e}")
        state["identified_tools"] = []  # 默认兜底

    return state


# ------------------------------------------------------------------------------

# 建议在外部维护 RAG 实例缓存
RAG_INSTANCES = {}

def rag_retrieval(state: AgentState) -> AgentState:
    """
    根据 tools_selector 识别出的工具列表，动态检索多个文档库。
    """
    # 1. 从 state 中获取之前节点识别出的工具列表
    # 如果 tools_selector 没选出工具，则默认 fallback 到 dorado
    identified_tools = state.get("identified_tools", [])

    if not identified_tools:
        print(f"\n[RAG] 未识别到工具，跳过检索流程。")
        state["rag_suggestion"] = {}
        return state

    user_query = state["input"]
    user_feedback = state.get("user_feedback", "")

    if user_feedback:
        user_query = f"初始需求: {user_query}\n用户最新追加/修改指令: {user_feedback}"

    print(f"\n[RAG] 正在为工具链 {identified_tools} 检索背景知识...")
    rag_llm = get_llm_instance(is_planner=False)

    # 2. 遍历工具列表，逐个检索
    rag_suggestion_dict = {}
    for tool in identified_tools:
        # 获取工具对应的文档路径 (从你定义的 TOOLS_MAPPING 中取)
        doc_path = TOOLS_DOC.get(tool)

        if not doc_path:
            print(f"[RAG] 警告: 未找到工具 {tool} 的文档路径映射，跳过。")
            continue

        # 3. 获取或创建检索器实例（单例模式，避免重复加载索引）
        if tool not in RAG_INSTANCES:
            print(f"[RAG] 正在初始化 {tool} 的检索索引...")
            RAG_INSTANCES[tool] = EnhancedMDRAG(doc_path, llm=rag_llm)

        retriever = RAG_INSTANCES[tool]

        # 4. 执行检索
        print(f"[RAG] 正在检索 {tool} 相关参数...")
        # 建议这里可以使用 user_query，或者针对该工具生成的特定 search_query
        context = retriever.search(user_query)

        # 将每个工具的检索结果打上明显的标签，方便 Planner 区分
        # tool_context = f"=== {tool.upper()} 官方文档参考 ===\n{context}"
        rag_suggestion_dict[tool.lower()] = context

    # 6. 更新 state，供下一步 Planner 使用
    state["rag_suggestion"] = rag_suggestion_dict

    return state
# ------------------------------------------------------------------------------

# 3. 工具规划节点 (占位符)
def tool_planner(state: AgentState) -> AgentState:
    """
    节点 1：流水线规划器 (Pipeline Planner)。
    只负责决定任务的先后执行顺序，不涉及任何参数生成。
    """

    # todo 后续要改成只调用一个工具，复杂的工具需要调用workflow
    planner_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    identified_tools = state.get("identified_tools", [])
    # user_feedback = state.get("user_feedback", "")
    history_str = format_history(state.get("chat_history", []))


    if not identified_tools:
        print(f"\n[Planner] 未识别到工具，跳过检索流程。")
        return state

    print(f"\n[Planner] 正在规划执行顺序，可用工具大类: {identified_tools}...")

    torch.cuda.empty_cache()

    prompt = ChatPromptTemplate.from_template("""
    你是一个生信流水线架构师。请根据用户需求，将任务分解为一系列连续的工具执行步骤。
    
    【重要】只规划用户明确要求的步骤，只规划用户明确要求的步骤。

    当前任务涉及的工具大类有: {identified_tools}

    请严格从以下具体命令中选择并排序：{tools_args}

    - 原始需求: {input}
    - 历史沟通轨迹: {history}
    
    你现在持有一个工具序列 [A, B, C]。用户现在说 D。请判断 D 是应该替换掉 C，还是接在 C 后面。如果是接在后面，请返回 [A, B, C, D]。

    请按执行顺序返回一个 JSON 列表。第一步的输出通常是第二步的输入。
    输出json格式: {{"sequence": ['工具1'，'工具2']}}。
    输出格式示例 (仅输出 JSON，勿带额外文本):
    {{
        "sequence": ["dorado_basecaller", "samtools_sort", "samtools_index", "samtools_fastq"]
    }}
    """)

    chain = prompt | planner_llm | JsonOutputParser()
    tools_args = []
    for t in identified_tools:
        tools_args.append(TOOL_ARGS.get(t.lower()))
    # print(f'tools_args {tools_args}')
    try:
        response = chain.invoke({
            "input": user_input,
            "history": history_str,
            "identified_tools": identified_tools,
            "tools_args": tools_args,
            # "rag_suggestion": state.get("rag_suggestion", "")
        })
        print(f'response {response}')

        state["tool_sequence"] = response.get("sequence", [])

        print(f"[Planner] 成功规划执行序列: {' -> '.join(state['tool_sequence'])}")
    except Exception as e:
        print(f"[Planner Error] 序列规划失败: {e}")
        state["tool_sequence"] = []

    return state

# ------------------------------------------------------------------------------

def parameter_generator(state: AgentState) -> AgentState:
    param_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    # 确保 rag_suggestion 是字典
    history_str = format_history(state.get("chat_history", []))
    rag_suggestion = state.get("rag_suggestion", {})
    tool_sequences = state.get("tool_sequence", [])

    print(f"\n[Param Generator] 正在为 {len(tool_sequences)} 个步骤配置参数...")

    if not tool_sequences:
        state["tool_calls"] = []
        return state

    user_feedback = state.get("user_feedback", "")
    old_tool_calls = state.get("tool_calls", [])
    final_tool_calls = []

    # 建议保存上一步的输出路径，而不是整个字典
    last_step_output_file = ""

    for i, tool_name in enumerate(tool_sequences):
        # 1. 基类映射逻辑（你的修改很棒！）
        tool_real_name = ''
        for t in TOOL_LIST:
            if t.lower() in tool_name.lower():
                tool_real_name = t.lower()
                break

        if not tool_real_name:
            print(f"  [Warning] 跳过无法识别的工具: {tool_name}")
            continue

        print(f"  > 正在配置第 {i + 1} 步: {tool_name} (base: {tool_real_name})")

        # 2. 获取 RAG 和 Schema
        current_rag = rag_suggestion.get(tool_real_name, "未找到相关 RAG 文档。")
        current_schema = str(TOOL_ARGS.get(tool_real_name, "{}"))

        # 3. 反馈逻辑处理
        last_params_snapshot = ""
        if old_tool_calls:
            for old_call in old_tool_calls:
                if tool_name.lower() == old_call.get("tool_name", "").lower():
                    last_params_snapshot = json.dumps(old_call.get("tool_args", {}), indent=2, ensure_ascii=False)
                    break

        # 4. 构造 Prompt（注意：这里规避了 f-string 对内部 JSON 的解析错误）
        # 使用 replace 填充大段 JSON，防止 f-string 崩溃
        base_prompt = """
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
        2. Dorado 规范：model 必须是完整版本号 (如 rna004_130bps_hac@v5.3.0)。
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

        # 安全填充变量
        final_prompt = base_prompt.format(
            step_num=i + 1,
            tool_name=tool_name,
            schema=current_schema,
            rag=current_rag,
            user_input=user_input,
            history=history_str,
            last_params=last_params_snapshot,
            user_feedback=user_feedback if user_feedback else "无",
            last_output=last_step_output_file
        )

        # print(f"[Debug] 当前 Prompt 长度: {len(final_prompt)} tokens\n{final_prompt}")

        try:
            torch.cuda.empty_cache()
            raw_response = param_llm.invoke(final_prompt)

            # 清洗 & 解析
            content = raw_response if isinstance(raw_response, str) else raw_response.content
            clean_json_str = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            if "```json" in clean_json_str:
                clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()

            current_call = json.loads(clean_json_str)
            print(f'\n[Param Generator] {current_call}')
            final_tool_calls.append(current_call)

            # 5. 提取 output 供下一步使用
            last_step_output_file = ""
            args = current_call.get("tool_args", {})
            if args:
                kwargs = args.get("kwargs",{})
                last_step_output_file = kwargs.get("output") or kwargs.get("output_file") or kwargs.get("output_dir") or kwargs.get("o") or ""

        except Exception as e:
            print(f"  [Error] {tool_name} 配置失败: {e}")
            continue

    state["tool_calls"] = final_tool_calls
    return state

# ------------------------------------------------------------------------------

def validator_node(state: AgentState) -> AgentState:
    """
    专家校验层：拦截 LLM 幻觉，进行参数的强制防御性校验和上下文衔接。
    """
    tool_calls = state.get("tool_calls", [])
    user_input = state.get("input", "").lower()

    if not tool_calls:
        return state

    for i, call in enumerate(tool_calls):
        tool_name = call.get("tool_name", "")
        tool_args  = call.get("tool_args", {})
        kwargs = tool_args.get("kwargs", {})
        pos_args = tool_args.get("pos_args", [])
        # ==========================================
        # 针对 Dorado 的专家规则
        # ==========================================
        if "basecall" in tool_name:
            extra = kwargs.get("extra_args", "")
            current_model = pos_args[0] if len(pos_args) > 0 else ""

            # 修 model（注意：现在 model 在 pos_args）
            if current_model in ["hac", "sup", "fast", ""] or len(current_model) < 10:
                if "dna" in user_input:
                    pos_args[0] = "dna_r10.4.1_e8.2_400bps_sup@v5.1.0"
                elif "rna002" in user_input:
                    pos_args[0] = "rna002_70bps_hac@v3.0.0"
                else:
                    pos_args[0] = "rna004_130bps_sup@v5.3.0"

                print(f"[Validator] 修正 model -> {pos_args[0]}")

            # 修 modified_bases
            mod = kwargs.get("modified-bases")

            if mod:
                if "--emit-moves" not in extra:
                    extra = f"{extra} --emit-moves".strip()

                if mod == "m6A_DRACH":
                    kwargs["modified-bases-models"] = f"{pos_args[0]}_m6A_DRACH@v1"

            kwargs["extra_args"] = extra

        # ==========================================
        # 针对 Samtools 的专家规则
        # ==========================================
        elif "samtools_sort" in tool_name:
            # 例如：确保 samtools sort 有合理的输出文件名
            if "sort" in tool_name and not kwargs.get("o"):
                kwargs["o"] = "sorted_output.bam"
                print("[Validator] 专家校验：自动补全 Samtools 排序输出文件名")

            # 如果是格式转换，确保参数中包含 -b
            if "view" in tool_name and ".bam" in kwargs.get("o", ""):
                extra = kwargs.get("extra_args", "")
                if "-b" not in extra:
                    kwargs["extra_args"] = f"{extra} -b".strip()

        tool_args["kwargs"] = kwargs
        tool_args["pos_args"] = pos_args

        # 回写修改后的参数
        call["tool_args"] = tool_args

    state["tool_calls"] = tool_calls
    return state

# ------------------------------------------------------------------------------

def human_review_node(state: AgentState) -> dict:
    tool_calls = state.get("tool_calls", [])

    history = state.get("chat_history", [])

    print("\n" + "=" * 30 + " 待执行任务确认 " + "=" * 30)
    for i, call in enumerate(tool_calls):
        tool_name = call['tool_name']
        tool_args = call['tool_args']

        kwargs = tool_args.get("kwargs", {})
        pos_args = tool_args.get("pos_args", [])

        # 1. 构建 CLI（但不执行）
        tool_name_array = tool_name.split('_')
        base_name = tool_name_array[0]
        last_sub_command = tool_name_array[-1]
        sub_cmd_str = " ".join(tool_name_array[1:])

        binary_name = f"{base_name} {sub_cmd_str}".strip()
        arg_str = build_shell_args(tool_args)

        print(f"\n步骤 {i + 1}: {tool_name}")
        print(f"\n结构化参数: {tool_args}")

        # 2. 人类可读解释
        verify_func = getattr(tools_verify, base_name, None)
        if verify_func:
            # 2. 执行校验函数。
            # 注意：我们将 wrapper.base_data_dir 传进去，方便函数决定输出到哪
            # todo 有了用户的概念和session的概念后这个数据目录应该改成具体的了
            raw_cmd = verify_func(last_sub_command, sub_cmd_str, tool_args, DATA_PATH[base_name])
        else:
            # 如果没有校验函数，使用通用拼接逻辑
            binary_name = f"{base_name} {sub_cmd_str}".strip()
            arg_str = build_shell_args(tool_args)
            raw_cmd = f"{binary_name} {arg_str}"

        # 3. CLI 命令（关键！）
        print("实际执行命令：")
        print(f"  {raw_cmd}")

    print("\n" + "=" * 76)

    user_input = input("\n[确认确认] 是否执行上述命令？(y/n) 或输入修改意见: ").strip()

    if user_input.lower() == 'y':
        history.append({"role": "user", "content": "确认执行，无需修改。"})
        return {
            "next_node": "executor",
            "user_approval": True,
            "user_feedback": "",
            "chat_history": history  # 返回更新后的历史
        }

    if user_input.lower() == 'exit':
        history.append({"role": "user", "content": "退出当前任务。"})
        return {"next_node": "end_node",  "chat_history": history}

    history.append({"role": "user", "content": f"用户修改意见：{user_input}"})


    identified_tools = state.get("identified_tools", [])

    llm = get_llm_instance(is_planner=True)
    prompt = f"""
        用户反馈: {user_input}
        当前已规划的步骤: {tool_calls}
        当前选取的工具: {identified_tools}

        请评估该反馈的影响范围，严格返回以下三个单词之一:
        - 'SELECTOR': 用户要求引入全新的软件大类（例如：原来只有dorado，现在要求使用samtools进行处理），如果用户新选取的工具不在已选工具中返回。
        - 'REPLAN': 涉及同一软件的逻辑步骤增减（例如：要求在原有的samtools sort之后，再加一步samtools index），如果用户新选取的工具在已选工具中返回。
        - 'REPARAM': 仅仅修改已有步骤的参数内容（例如：修改输入输出路径、修改模型版本、添加--reference文件），不增加任何新步骤。

        只返回一个单词，不要有任何其他字符。
        """
    raw_decision = llm.invoke(prompt)
    decision_text = raw_decision.content if hasattr(raw_decision, "content") else str(raw_decision)
    decision = decision_text.replace("'", "").replace('"', '').replace(".", "").strip().upper()

    mapping = {
        "SELECTOR": "tools_selector",
        "REPLAN": "rag",
        "REPARAM": "param_generator",
    }

    return {
        "next_node": mapping.get(decision, "param_generator"),
        "user_feedback": user_input,
        "chat_history": history  # 带着新记忆进入下一轮
    }



# ------------------------------------------------------------------------------

def execute_tool(state: AgentState) -> dict:
    """
    执行规划好的工具，并处理输出。
    """
    wrapper = EnvWrapper()
    executor = ToolExecutor()

    tool_calls = state.get("tool_calls", [])
    execution_results = []
    history = state.get("chat_history", [])
    next_node = "summarizer"
    tool_output = []
    for call in tool_calls:
        tool_name = call['tool_name']
        args = call['tool_args']

        # 1. 简单的参数转换逻辑 (根据你的 Agent 输出习惯调整)
        # 这里假设 tool_name 对应容器内的二进制文件名
        tool_name_array = tool_name.split('_')
        base_name = tool_name_array[0]
        sub_cmd_str = " ".join(tool_name_array[1:])
        last_sub_command = tool_name_array[-1]
        if base_name not in TOOL_LIST:
            # tools_selector
            history.append({"role": "assistant", "content": f"工具：{base_name}不在系统中，请重新规划选择。"})
            return {
                "chat_history": history,
                # 这里你可以根据 any_failed 返回不同的 next_node 标志
                "next_node": "tools_selector"
            }

        # 特定子命令校验
        verify_func = getattr(tools_verify, base_name, None)
        if verify_func:
            # 2. 执行校验函数。
            # 注意：我们将 wrapper.base_data_dir 传进去，方便函数决定输出到哪
            # todo 有了用户的概念和session的概念后这个数据目录应该改成具体的了
            raw_cmd = verify_func(last_sub_command, sub_cmd_str, args, DATA_PATH[base_name])
        else:
            # 如果没有校验函数，使用通用拼接逻辑
            binary_name = f"{base_name} {sub_cmd_str}".strip()
            arg_str = build_shell_args(args)
            raw_cmd = f"{binary_name} {arg_str}"

        if 'error' in raw_cmd.lower():
            error_msg = f"工具 {tool_name} 预校验失败: {raw_cmd}"
            execution_results.append(error_msg)
            # 写入记忆：告诉 LLM 它的参数构造逻辑不对
            history.append({"role": "assistant", "content": f"系统拦截：{error_msg}，请重新配置参数。"})
            break

        # 2. 封装与执行
        print(f"\n[Executor] 正在执行: {raw_cmd}")
        final_cmd = wrapper.wrap_command(base_name, raw_cmd)
        print(f"\n[Executor] 真实执行: {final_cmd}")
        resp = executor.run(final_cmd)

        # 3. 结果处理
        if resp["status"] == "success":
            output = resp.get("output", "")
            success_log = output[-200:]
            success_msg = f"{tool_name} 成功\n输出摘要: {success_log}"
            execution_results.append(success_msg)
            # state['tool_output'] = output[:2000]
            print(f"\n[Executor] {success_msg}")
            tool_output.append(output)
            history.append({"role": "assistant", "content": f"{success_msg} 输出路径已记录。"})
        else:
            next_node = "param_generator"
            error_log = resp['stderr'][:500] + "\n...\n" + resp['stderr'][-500:]
            fail_msg = f"{tool_name} 执行失败！报错信息:\n{error_log}"
            execution_results.append(fail_msg)
            print(f"\n[Executor] 执行失败: {fail_msg}")
            # 【关键点】：把报错塞进历史记录！
            # 这样当下一次回到 param_generator 时，LLM 就能看到为什么失败了。
            history.append({
                "role": "assistant",
                "content": f"我尝试执行了 {tool_name}，但失败了。报错如下：\n{error_log}\n我需要根据这个错误修正参数。"
            })
            break  # 一步错步步错，通常生信流水线第一个错就该停下

    return {
        "chat_history": history,
        # 这里你可以根据 any_failed 返回不同的 next_node 标志
        "next_node":  next_node,
        "tool_output": tool_output

    }
# ------------------------------------------------------------------------------

def general_llm_answer(state: AgentState) -> AgentState:
    """
    调用 LLM 回答基础知识问题。
    """
    user_input = state["input"]
    print(f"\n[LLM Answer] 正在调用 LLM 回答基础问题: {user_input[:20]}...")
    answer_llm = get_llm_instance(is_planner=False)
    # 实际调用 LLM
    try:
        # 使用 LLM 的 invoke 方法，直接获取回答
        llm_response = answer_llm.invoke(user_input)

        # 将 LLM 的回答设置为最终答案
        state["final_answer"] = llm_response.strip()

    except Exception as e:
        print(f"LLM 调用失败: {e}")
        state["final_answer"] = "抱歉，LLM 服务暂时不可用，无法回答您的问题。"
    print(f'\n[LLM Answer] {state["final_answer"]}')
    return state

# ------------------------------------------------------------------------------


# 5. 结果总结节点 (占位符)
def output_summarizer(state: AgentState) -> AgentState:
    """
    LLM 总结 RAG 结果或工具输出，生成最终答案。
    """
    tool_calls = state.get("tool_calls", [])
    tool_output = state.get("tool_output", [])
    if not tool_calls:
        return state

    print("\n[Summarizer] 正在总结最终答案...")
    output = '\n'.join(tool_output)
    summary = f"根据您的需求，已成功执行操作。工具输出结果：{output}. 请查看文件。"
    state["final_answer"] = summary
    print(f'\n[LLM Answer] {state["final_answer"]}')
    return state

# ------------------------------------------------------------------------------

# 6. 非相关回复节点 (占位符)
def non_relevant_response(state: AgentState) -> AgentState:
    """
    生成一个礼貌的非相关回复。
    """
    print("\n[Irrelevant] 生成不相关回复...")
    state["final_answer"] = "抱歉，我专注于纳米孔测序和修饰检测相关的任务，无法为您提供该信息。"
    print(f'\n[LLM Answer] {state["final_answer"]}')

    return state


def end_node(state: AgentState) -> AgentState:
    """
    生成一个礼貌的非相关回复。
    """
    print(f'\n[End] 本次会话结束')

    return state