
"""
问答节点 - 支持Web搜索增强
需要依赖: pip install ddgs html2text beautifulsoup4
"""
from agent_graph.state import AgentState
from utils.llm_utils import get_llm_instance
from utils.search_utils import SearchAugmentedQA

# 多层级导入保证兼容性
try:
    from utils.ui_logger import ui_print
except ImportError:
    try:
        # 从 agent_graph/nodes/execution/response.py 向上3层到项目根目录
        from ....utils.ui_logger import ui_print
    except ImportError:
        # 降级：没有 ui_logger 就用普通 print
        ui_print = print

def answer_general_question_node(state: AgentState, use_search: bool = True, num_searches: int = 5) -> AgentState:
    """
    问答节点 - 支持Web搜索增强
    参数:
      use_search: 启用搜索增强 (default: True)
      num_searches: 搜索结果数 (default: 5)
    流程: 搜索 → 爬取 → 转MD → RAG → LLM回答 → 清理
    """
    user_input = state["input"]
    augmented_context = ""
    qa_tool = None
    
    try:
        # 1. 可选：Web搜索和RAG增强
        if use_search:
            ui_print(f"\n[Search] 正在搜索和检索相关信息...")
            qa_tool = SearchAugmentedQA()
            
            try:
                augmented_context = qa_tool.augment_query(user_input, num_searches=num_searches)
                if augmented_context:
                    ui_print(f"[Search] 成功获取搜索结果上文 ({len(augmented_context)} 字符)")
                else:
                    ui_print(f"[Search] 搜索未返回结果，继续使用纯LLM回答")
            except Exception as e:
                ui_print(f"[Search] 搜索异常: {type(e).__name__}，继续使用纯LLM回答")
                augmented_context = ""
        
        # 2. 构建最终提示词
        if augmented_context:
            final_prompt = f"""请根据以下搜索结果回答用户问题：

            【搜索结果和相关文档】
            {augmented_context}

            【用户问题】
            {user_input}

            请基于上述信息提供准确、详细的回答。"""
        else:
            final_prompt = user_input
        
        # 3. 调用LLM
        ui_print(f"\n[LLM Answer] 正在调用 LLM 回答问题: {user_input[:30]}...")
        answer_llm = get_llm_instance(is_planner=False)
        
        llm_response = answer_llm.invoke(final_prompt)
        llm_response = llm_response.strip()
        
        # 清理 <think>...</think> 思维过程标签
        if '<think>' in llm_response:
            import re
            llm_response = re.sub(r'<think>.*?</think>', '', llm_response, flags=re.DOTALL)
            llm_response = llm_response.strip()
        
        state["final_answer"] = llm_response
        
    except Exception as e:
        ui_print(f"[LLM Answer] 调用失败: {e}")
        state["final_answer"] = "抱歉，服务暂时不可用，无法回答您的问题。"
    
    finally:
        # 4. 清理临时文件
        if qa_tool:
            try:
                qa_tool.cleanup()
                ui_print("[Cleanup] 临时文件已清理")
            except Exception as e:
                ui_print(f"[Cleanup] 清理失败: {e}")
    
    # 输出完整回答
    answer = state["final_answer"]
    if not answer:
        answer = "（无内容）"
    
    # 输出回答，限制控制台显示长度
    if len(answer) > 1000:
        ui_print(f'\n[LLM Answer]\n{answer[:1000]}\n...\n[更多内容已生成，共 {len(answer)} 字符]')
    else:
        ui_print(f'\n[LLM Answer]\n{answer}')
    
    return state


def summarize_execution_result_node(state: AgentState) -> AgentState:
    tool_calls = state.get("tool_calls", [])
    tool_output = state.get("tool_output", [])
    if not tool_calls:
        return state

    ui_print("\n[Summarizer] 正在总结最终答案...")
    output = "\n".join(tool_output)
    summary = f"根据您的需求，已成功执行操作。工具输出结果：{output}. 请查看文件。"
    state["final_answer"] = summary
    ui_print(f'\n[LLM Answer] {state["final_answer"]}')
    return state

def handle_irrelevant_request_node(state: AgentState) -> AgentState:
    ui_print("\n[Irrelevant] 生成不相关回复...")
    state["final_answer"] = "抱歉，我专注于纳米孔测序和修饰检测相关的任务，无法为您提供该信息。"
    ui_print(f'\n[LLM Answer] {state["final_answer"]}')
    return state


def finish_session_node(state: AgentState) -> AgentState:
    ui_print(f"\n[End] 本次会话结束")
    return state

