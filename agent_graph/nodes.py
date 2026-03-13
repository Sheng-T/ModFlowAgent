# 假设你的 LLM 已经通过 HuggingFacePipeline 实例化
# from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
# llm = HuggingFacePipeline(...)
import re
from typing import TypedDict
from agent_graph.state import AgentState, EMPTY_STATE
import os
import sys

from data_storage.rag_retriever import EnhancedMDRAG

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
from utils.common_utils import LLM_SOURCE, LLM_NAME, llm_model_path, TOOL_LIST, TOOLS_DOC, TOOL_ARGS, llm_args
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
# from langchain.output_parsers import PydanticOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import json
from typing import TYPE_CHECKING

import logging

logging.getLogger("transformers").setLevel(logging.ERROR)

# 简化占位符 LLM

def import_llm_initializer(module_name: str, function_name: str = "get_llm"):
    """
    动态导入指定模块中的 LLM 初始化函数。

    Args:
        module_name: 模块名称 (例如 "qwen_model")。
        function_name: 要导入的函数名称 (例如 "get_llm")。

    Returns:
        导入的函数对象 (Callable)。
    """
    # 构造完整的模块路径，例如: agent.LLM.qwen_model
    full_module_path = f"LLM.{module_name}"

    try:
        # 尝试使用 importlib 导入模块
        spec = importlib.util.find_spec(full_module_path)
        if spec is None:
            raise ModuleNotFoundError(f"无法找到模块: {full_module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_path] = module
        spec.loader.exec_module(module)

        # 从模块中获取指定的函数
        if not hasattr(module, function_name):
            raise AttributeError(f"模块 '{module_name}' 中没有找到函数 '{function_name}'。")

        return getattr(module, function_name)

    except (ModuleNotFoundError, AttributeError) as e:
        print(f"致命错误：动态导入 LLM 失败: {e}")
        raise e


_MODEL_CACHE = {}
def get_llm_instance(is_planner: bool = False, temperature=0.01):
    """
    根据用途获取 LLM 实例。
    is_planner: True 则获取低随机性、关闭思考的 Planner 专用模型。
    """
    global _MODEL_CACHE

    if "llm" not in _MODEL_CACHE:
        print("[System] 首次初始化模型，请稍候...")
        llm_func = import_llm_initializer(module_name=LLM_NAME)
        llm_path = llm_model_path[LLM_NAME]
        # 这里只加载一次
        _MODEL_CACHE["llm"] = llm_func(llm_path, device=llm_args['device'])

    model = _MODEL_CACHE["llm"]
    if is_planner:
        model.temperature = 0.01
        model.enable_thinking = False
    else:
        model.temperature = 0.7
        model.enable_thinking = True
    return model



from pydantic import BaseModel, Field
from typing import List

# 定义单个工具调用的结构
class ToolCall(BaseModel):
    """一个规划中的工具调用。"""
    tool_name: str = Field(..., description="要调用的工具名称，必须从可用工具列表中选择。")
    tool_args: dict = Field(..., description="工具所需的参数，键必须与工具定义中的 'args' 匹配。")

# 定义最终的输出结构，它是一个 ToolCall 对象的列表
class ToolPlan(BaseModel):
    """LLM 规划的工具执行列表。"""
    plan: List[ToolCall] = Field(..., description="要按顺序执行的工具调用列表。")
    is_tool_needed: bool = Field(..., description="如果用户需求完全可以通过工具解决，则为 True；如果只需要 RAG 或简单总结，则为 False。")

# 1. 意图路由/决策节点

# 节点函数本身现在只需要返回 state
def intent_router(state: AgentState) -> AgentState:
    """
    意图路由/决策节点。
    此函数仅作为节点执行，不进行路由决策，路由决策由 router_selector 负责。
    如果需要，可以在此提取 data_path 或做其他状态初始化。
    """
    user_input = state["input"]
    print(f"\n[Router] 正在分析用户输入: '{user_input[:30]}...'")

    return {**EMPTY_STATE, "input": state["input"]}

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
    tool_sequence = state.get("tool_sequence", [])
    print(f"\n[Tools Selector] 正在分析任务涉及的工具...")

    # 1. 构造工具描述，让 LLM 了解每个工具能干什么
    tools_info = "\n".join([f"- {t['name']}: {t['description']}" for t in TOOL_LIST])

    if user_feedback:
        user_input = f"初始需求: {user_input}\n用户最新追加/修改指令: {user_feedback}\n之前构建的命令: {tool_sequence}\n非必要最好不要动之前的命令，在这个命令的基础上重新调整增加/删除工具"

    # 2. 构造 Prompt
    prompt = ChatPromptTemplate.from_template("""
    你是一个生信流程调度专家。请分析用户的需求，从下方的工具列表中挑选出完成任务所需的【所有】工具。

    【可选工具列表】:
    {tools_info}

    【任务逻辑参考】:
    - 如果涉及测序数据转序列、碱基识别、修饰检测（m6A/5mC）、summary、序列比对，必须选择 'dorado'。
    - 如果涉及结果文件的排序 (sort)、索引 (index)、格式转换 (BAM/SAM)、统计 (stats)，必须选择 'samtools'。

    用户需求: {input}

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
            "tools_info": tools_info
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
        state["rag_suggestion"] = "无可用工具文档。"
        return state

    user_query = state["input"]
    print(f"\n[RAG] 正在为工具链 {identified_tools} 检索背景知识...")
    rag_llm = get_llm_instance(is_planner=False)
    all_contexts = []

    # 2. 遍历工具列表，逐个检索
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
        tool_context = f"=== {tool.upper()} 官方文档参考 ===\n{context}"
        all_contexts.append(tool_context)

    # 5. 合并所有检索到的信息
    if all_contexts:
        combined_suggestion = "\n\n".join(all_contexts)
    else:
        combined_suggestion = "未找到相关工具的详细说明文档。"

    # 打印调试信息（可选）
    print(f"[RAG] {'=' * 20} 检索汇总 {'=' * 20}")
    print(combined_suggestion[:500] + "..." if len(combined_suggestion) > 500 else combined_suggestion)
    print(f"{'=' * 50}\n")

    # 6. 更新 state，供下一步 Planner 使用
    state["rag_suggestion"] = combined_suggestion

    return state
# ------------------------------------------------------------------------------

def print_llm_output(output: str) -> str:
    """打印 LLM 的原始文本输出"""
    print("\n--- LLM 原始输出 (DEBUG) ---")
    print(output)
    print("----------------------------\n")
    return output

def extract_json(message: str) -> str:
    text = message
    # ... (打印 debug 信息) ...
    # print_llm_output(text)
    # 使用修正后的表达式
    pattern = r"```(?:json)?\s*({.*?})\s*```"
    matches = re.findall(pattern, text, re.DOTALL)

    # 优先处理 Markdown 块
    if matches:
        # 核心修改：返回最后一个匹配到的 JSON 字符串，让 parser 去解析
        m = matches[-1].strip()
        print(m)
        return m

    # 如果没有 Markdown 块，尝试提取并返回裸露的 JSON 字符串
    start = text.find('{')
    end = text.rfind('}')

    if start != -1 and end != -1:
        potential_json_str = text[start:end + 1]

        # 在返回前进行一次快速验证，确保它是一个有效的 JSON 字符串，避免在 parser 处崩溃
        try:
            json.loads(potential_json_str)
            print(potential_json_str)
            return potential_json_str
        except json.JSONDecodeError:
            pass  # 验证失败，继续抛出错误

    # 如果所有提取都失败，则抛出错误
    raise ValueError(f"Failed to find or parse any valid JSON block in the LLM output.")

# 3. 工具规划节点 (占位符)
def tool_planner(state: AgentState) -> AgentState:
    """
    节点 1：流水线规划器 (Pipeline Planner)。
    只负责决定任务的先后执行顺序，不涉及任何参数生成。
    """
    planner_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    identified_tools = state.get("identified_tools", [])
    user_feedback = state.get("user_feedback", "")
    tool_sequence = state.get("tool_sequence", [])
    if user_feedback:
        user_input = f"初始需求: {user_input}\n用户最新追加/修改指令: {user_feedback}\n之前构建的命令: {tool_sequence}"

    if not identified_tools:
        print(f"\n[Planner] 未识别到工具，跳过检索流程。")
        return state

    print(f"\n[Planner] 正在规划执行顺序，可用工具大类: {identified_tools}...")

    prompt = ChatPromptTemplate.from_template("""
    你是一个生信流水线架构师。请根据用户需求，将任务分解为一系列连续的工具执行步骤。

    当前任务涉及的工具大类有: {identified_tools}

    请严格从以下具体命令中选择并排序：{tools_args}
    
    RAG 官方文档参考：{rag_suggestion}

    用户需求: {input}

    请按执行顺序返回一个 JSON 列表。第一步的输出通常是第二步的输入。
    输出json格式{{"sequence": ['工具1'，'工具2']}}。
    输出格式示例 (仅输出 JSON，勿带额外文本):
    {{
        "sequence": ["dorado_basecaller", "samtools_sort", "samtools_index"]
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
            "identified_tools": identified_tools,
            "tools_args": tools_args,
            "rag_suggestion": state.get("rag_suggestion", "")
        })
        print(f'response {response}')

        state["tool_sequence"] = response.get("sequence", [])
        state["tool_args_schema"] = tools_args

        print(f"[Planner] 成功规划执行序列: {' -> '.join(state['tool_sequence'])}")
    except Exception as e:
        print(f"[Planner Error] 序列规划失败: {e}")
        state["tool_sequence"] = []

    return state

# ------------------------------------------------------------------------------

def parameter_generator(state: AgentState) -> AgentState:
    """
    节点 2：参数生成器 (Parameter Generator)。
    负责根据规划和 RAG 建议填充具体参数，并响应用户反馈。
    """
    param_llm = get_llm_instance(is_planner=True)
    user_input = state["input"]
    rag_suggestion = state.get("rag_suggestion", "")
    tool_sequence = state.get("tool_sequence", [])
    tool_args_schema = state.get("tool_args_schema", "[]")  # 建议从 state 或 common_utils 获取

    print(f"\n[Param Generator] 正在为 {len(tool_sequence)} 个步骤配置参数...")

    if not tool_sequence:
        state["tool_calls"] = []
        return state

    # 处理用户反馈（用于打回重做时的修正）
    user_feedback = state.get("user_feedback", "")
    feedback_context = ""
    if user_feedback:
        tool_calls = state.get("tool_calls", [])
        # 将历史 tool_calls 转换为清晰的 JSON 字符串让 LLM 参考
        history_json = json.dumps(tool_calls, indent=2, ensure_ascii=False)
        feedback_context = f"\n【重要历史状态】：上一次生成的参数如下：\n{history_json}\n【用户最新反馈】：{user_feedback}\n 请在上述历史状态的基础上进行局部修改！"

    # 构造更加严谨的 Prompt
    prompt = ChatPromptTemplate.from_template("""
    你是一个精通生信命令行（Dorado/Samtools）的参数配置专家。
    任务序列：{tool_sequence}。

    【核心指令】:
    1. 结合用户需求、RAG 文档和下方反馈（如有），填充具体参数。
    2. **历史继承原则 (极度重要)**：如果存在【用户反馈】，你必须原样保留 {feedback_context} 中已经配置正确的参数值（如果为空请忽略）！只能针对用户的反馈修改对应的参数，绝对禁止将之前已经识别出来的参数（如模型名、路径、修饰类型）重置为空！
    3. **宁缺毋滥原则**：如果用户未指定 input 路径、model 版本等关键参数，且 RAG 无法推断，请将值设为 "" (空字符串)。禁止捏造路径！
    4. **上下文衔接**：前一步的 output_file 必须是后一步的 input。
    5. **Dorado 规范**：model 必须是完整版本号 (如 rna004_130bps_hac@v5.3.0)，不能简写为 'hac'。

    【工具参数定义 Schema】:
    {tool_args_schema}

    【RAG 官方文档参考】:
    {rag_suggestion}
    {feedback_context}

    用户原始需求: {input}

    请输出严格的 JSON 格式（不要包含 <think> 或额外文本）:
    {{
        "tool_calls": [
            {{
                "tool_name": "具体工具名",
                "tool_args": {{ "key": "value" }}
            }}
        ]
    }}
    """)

    # 改进点：在 invoke 之前增加过滤逻辑，处理 LLM 可能自带的 <think> 标签
    chain = prompt | param_llm

    try:
        # 1. 运行 LLM
        raw_response = chain.invoke({
            "input": user_input,
            "tool_sequence": tool_sequence,
            "tool_args_schema": tool_args_schema,
            "rag_suggestion": rag_suggestion,
            "feedback_context": feedback_context
        })

        # 2. 清洗可能存在的 <think> 标签或 Markdown 格式（鲁棒性处理）
        content = raw_response if isinstance(raw_response, str) else raw_response.content
        clean_json_str = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 3. 手动调用 JsonOutputParser 确保解析成功
        parser = JsonOutputParser()
        response_dict = parser.parse(clean_json_str)

        state["tool_calls"] = response_dict.get("tool_calls", [])
        print(f"[Param Generator] 参数配置完成。")

    except Exception as e:
        print(f"[Param Generator Error] 参数生成解析失败: {e}")
        state["tool_calls"] = []

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
        args = call.get("tool_args", {})

        # ==========================================
        # 针对 Dorado 的专家规则
        # ==========================================
        if "dorado" in tool_name:
            extra = args.get("extra_args", "")
            current_model = args.get("model", "")

            # 1. 核心模型名称防幻觉修正 (自动适配 RNA004/RNA002 跨平台需求)
            if current_model in ["hac", "sup", "fast", ""] or len(current_model) < 10:
                if "dna" in user_input:
                    args["model"] = "dna_r10.4.1_e8.2_400bps_hac@v4.3.0"
                elif "rna002" in user_input:
                    args["model"] = "rna002_70bps_hac@v3.0.0"
                    print("[Validator] 规则匹配：检测到 RNA002 跨平台评估需求，已切换测序化学模型。")
                else:
                    args["model"] = "rna004_130bps_hac@v5.3.0"  # 默认 RNA
                print(f"[Validator] 专家校验：已将模糊模型名强制修正为 '{args['model']}'")

            # 2. 动态构建 Site-level 修饰检测模型路径
            mod = args.get("modified_bases")
            has_mod = mod or args.get("modified_bases_models")

            if has_mod:
                if not args.get("modified_bases"):
                    # 如果用户没填，说明不需要，不要自动补全！
                    continue

                if "--emit-moves" not in extra:
                    print("[Validator] 规则匹配：执行修饰分析必须包含信号级移位，注入 --emit-moves")
                    extra = f"{extra} --emit-moves".strip()

                # 根据主模型自动拼接修饰模型，确保版本严格一致
                if mod == "m6A_DRACH":
                    args["modified_bases_models"] = f"{args['model']}_m6A_DRACH@v1"
                elif mod == "m6A":
                    args["modified_bases_models"] = f"{args['model']}_m6A@v1"

                print(f"[Validator] 专家校验：修饰模型校准为 {args.get('modified_bases_models')}")

            # 3. 输出格式与路径防御
            if "--emit-sam" in extra:
                print("[Validator] 规则匹配：移除 --emit-sam 以保护输出格式")
                extra = re.sub(r'\s*--emit-sam\s*', ' ', extra).strip()

            if not args.get("output_dir"):
                print("[Validator] 警告：补全缺失的 output_dir")
                args["output_dir"] = "./dorado_out"

            args["extra_args"] = extra

        # ==========================================
        # 针对 Samtools 的专家规则
        # ==========================================
        elif "samtools" in tool_name:
            # 例如：确保 samtools sort 有合理的输出文件名
            if "sort" in tool_name and not args.get("output_file"):
                args["output_file"] = "sorted_output.bam"
                print("[Validator] 专家校验：自动补全 Samtools 排序输出文件名")

            # 如果是格式转换，确保参数中包含 -b
            if "view" in tool_name and ".bam" in args.get("output_file", ""):
                extra = args.get("extra_args", "")
                if "-b" not in extra:
                    args["extra_args"] = f"{extra} -b".strip()

        # 回写修改后的参数
        call["tool_args"] = args

    state["tool_calls"] = tool_calls
    return state

# ------------------------------------------------------------------------------

def human_review_node(state: AgentState) -> dict:
    tool_calls = state.get("tool_calls", [])

    print("\n" + "=" * 30 + " 待执行任务确认 " + "=" * 30)
    for i, call in enumerate(tool_calls):
        print(f"步骤 {i + 1}: {call['tool_name']}")
        print(f"参数配置: {json.dumps(call['tool_args'], indent=4, ensure_ascii=False)}")
    print("=" * 76)

    user_input = input("\n[确认确认] 是否执行上述命令？(y/n) 或输入修改意见: ").strip()

    if user_input.lower() == 'y':
        state["user_approval"] = True
        state["user_feedback"] = ""
        return {"next_node": "executor", "user_approval": True}

    state["user_approval"] = False
    state["user_feedback"] = user_input

    llm = get_llm_instance(is_planner=True)
    prompt = f"""
        用户反馈: {user_input}
        当前已规划的步骤: {tool_calls}

        请评估该反馈的影响范围，严格返回以下三个单词之一:
        - 'SELECTOR': 用户要求引入全新的软件大类（例如：原来只有dorado，现在要求使用samtools进行处理）。
        - 'REPLAN': 涉及同一软件的逻辑步骤增减（例如：要求在原有的samtools sort之后，再加一步samtools index）。
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
        "user_approval": False,
        "user_feedback": user_input
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


# 4. 工具执行节点 (占位符)
def execute_tool(state: AgentState) -> AgentState:
    """
    执行规划好的工具，并处理输出。
    """
    print(f"\n[Execute] 正在执行工具: {state['tool_calls']}")

    tool_calls = state.get("tool_calls", [])
    execution_results = []

    for call in tool_calls:
        # 这里放置你调用真实 subprocess 的逻辑
        # ...
        execution_results.append(f"{call['tool_name']} 成功完成")

    state["tool_output"] = "; ".join(execution_results)
    state["tool_calls"] = []  # 清空
    return state

# ------------------------------------------------------------------------------


# 5. 结果总结节点 (占位符)
def output_summarizer(state: AgentState) -> AgentState:
    """
    LLM 总结 RAG 结果或工具输出，生成最终答案。
    """
    tool_calls = state.get("tool_calls", [])
    if not tool_calls:
        return state

    print("\n[Summarizer] 正在总结最终答案...")

    summary = f"根据您的需求，已成功执行操作。工具输出结果：{state['tool_output']}. 请查看文件。"
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