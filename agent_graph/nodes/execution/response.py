
"""
问答节点 - 支持Web搜索增强
需要依赖: pip install ddgs html2text beautifulsoup4
"""
from agent_graph.state import AgentState
from agent_graph.prompts.qa_prompts import build_qa_prompt
from utils.llm_utils import get_llm_instance
from utils.search_utils import SearchAugmentedQA
from utils.lang_utils import get_lang
from utils.ui_logger import ui_print


def answer_general_question_node(state: AgentState, use_search: bool = True, num_searches: int = 5) -> AgentState:
    """Q&A node with optional web-search augmentation."""
    import re

    user_input = state["input"]
    augmented_context = ""
    qa_tool = None

    # detect current UI language
    try:
        import streamlit as st
        lang = st.session_state.get("lang", "en_US")
    except Exception:
        lang = "en_US"

    try:
        # 1. optional web search
        if use_search:
            ui_print(f"\n[Search] Fetching reference material...")
            qa_tool = SearchAugmentedQA()
            try:
                augmented_context = qa_tool.augment_query(user_input, num_searches=num_searches)
                if augmented_context:
                    ui_print(f"[Search] Retrieved {len(augmented_context)} chars of context")
                else:
                    ui_print("[Search] No results — falling back to LLM knowledge")
            except Exception as e:
                ui_print(f"[Search] Error ({type(e).__name__}), falling back to LLM knowledge")
                augmented_context = ""

        # 2. build prompt
        final_prompt = build_qa_prompt(user_input, augmented_context, lang)

        # 3. call LLM
        ui_print(f"\n[LLM Answer] Invoking LLM: {user_input[:40]}...")
        answer_llm = get_llm_instance(is_planner=False)
        llm_response = answer_llm.invoke(final_prompt)
        llm_response = llm_response.strip() if isinstance(llm_response, str) else llm_response.content.strip()
        llm_response = re.sub(r"<think>.*?</think>", "", llm_response, flags=re.DOTALL).strip()

        state["final_answer"] = llm_response

    except Exception as e:
        ui_print(f"[LLM Answer] Failed: {e}")
        state["final_answer"] = (
            "Sorry, the service is temporarily unavailable." if lang == "en_US"
            else "抱歉，服务暂时不可用，无法回答您的问题。"
        )

    finally:
        if qa_tool:
            try:
                qa_tool.cleanup()
            except Exception:
                pass

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
    import json
    import os
    import re

    from tools.analyzers.registry import (
        extract_output_paths,
        get_file_analyzer,
        FUNCTIONAL_ANALYZER_MENU,
        get_functional_analyzer,
    )
    from utils.user_context import get_session_dir

    lang = get_lang()

    tool_calls        = state.get("tool_calls", [])
    tool_output       = state.get("tool_output", [])
    pending_commands  = state.get("pending_commands", [])
    run_dir           = state.get("run_dir", "")

    if not tool_calls:
        return state

    ui_print("\n[Summarizer] 开始两层分析流程...")
    llm = get_llm_instance(is_planner=False)

    # ── 步骤 1：从命令中提取输出文件路径 ──────────────────────────────────────
    output_paths = extract_output_paths(pending_commands)
    ui_print(f"[Summarizer] 检测到输出文件: {output_paths}")

    # ── 步骤 2：文件分析（按后缀确定性执行，不调用 LLM）─────────────────────
    file_stats_map: dict[str, dict] = {}   # file_path → stats dict
    for path in output_paths:
        analyzer = get_file_analyzer(path)
        if analyzer is None:
            ui_print(f"[Summarizer] 无对应文件分析器，跳过: {os.path.basename(path)}")
            continue
        ui_print(f"[Summarizer] 分析文件: {os.path.basename(path)}")
        stats = analyzer.analyze(path)
        file_stats_map[path] = stats
        ui_print(f"[Summarizer] 文件统计完成: {stats.get('type', '?')} — {len(stats)} 个指标")

    # ── 步骤 3：LLM 从菜单中选择功能分析模块 ─────────────────────────────────
    tool_desc = ", ".join(c["tool_name"] for c in tool_calls)
    menu_text = "\n".join(
        f'- {item["name"]}: {item["description"]}'
        for item in FUNCTIONAL_ANALYZER_MENU
    )
    if lang == "en_US":
        select_prompt = (
            f"Tools executed: {tool_desc}\n\n"
            f"Available analysis modules:\n{menu_text}\n\n"
            f"Select all modules relevant to the tools that were executed.\n"
            f"Return JSON only: {{\"selected\": [\"module_name1\", \"module_name2\"]}}"
        )
    else:
        select_prompt = (
            f"已执行的工具：{tool_desc}\n\n"
            f"可用功能分析模块：\n{menu_text}\n\n"
            f"请根据执行的工具，从上述模块中选出所有相关的功能分析模块。\n"
            f"只返回 JSON，格式：{{\"selected\": [\"module_name1\", \"module_name2\"]}}"
        )
    selected_modules: list[str] = []
    try:
        raw = llm.invoke(select_prompt)
        content = raw if isinstance(raw, str) else raw.content
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        if "```" in content:
            content = content.split("```")[1].lstrip("json").strip()
        parsed = json.loads(content)
        selected_modules = parsed.get("selected", [])
        ui_print(f"[Summarizer] LLM 选择功能模块: {selected_modules}")
    except Exception as e:
        ui_print(f"[Summarizer] 功能模块选择失败: {e}，将跳过功能分析")

    # ── 步骤 4：功能分析（规则判断，不调用 LLM）──────────────────────────────
    functional_results: list[dict] = []
    for module_name in selected_modules:
        analyzer = get_functional_analyzer(module_name)
        if analyzer is None:
            continue
        # 找到对应类型的文件统计
        menu_item  = next((m for m in FUNCTIONAL_ANALYZER_MENU if m["name"] == module_name), {})
        need_type  = menu_item.get("required_stat_type", "")
        stats_input = next(
            (s for s in file_stats_map.values() if s.get("type") == need_type),
            None,
        )
        if stats_input is None:
            ui_print(f"[Summarizer] 跳过 {module_name}：无匹配的 {need_type} 文件统计")
            continue
        ui_print(f"[Summarizer] 运行功能分析: {module_name}")
        result = analyzer.analyze(stats_input)
        functional_results.append(result)

    # ── 步骤 5：LLM 生成自然语言报告 ─────────────────────────────────────────
    # 过滤掉原始错误字段，避免 LLM 把内部错误信息当作报告内容输出
    _error_keys = {"flagstat_error", "stats_error", "error"}
    clean_stats_map = {
        path: {k: v for k, v in stats.items() if k not in _error_keys}
        for path, stats in file_stats_map.items()
    }

    stats_json      = json.dumps(clean_stats_map,      ensure_ascii=False, indent=2)
    func_json       = json.dumps(functional_results,   ensure_ascii=False, indent=2)
    raw_output_text = "\n".join(tool_output).strip()[:1000]

    if lang == "en_US":
        report_prompt = f"""You are a bioinformatics expert. Generate a professional report based on the analysis results below.

[Tools Executed]: {tool_desc}
[Raw Tool Output (summary)]:
{raw_output_text}

[File Statistics]:
{stats_json}

[Functional Analysis Results]:
{func_json}

[Background]:
- BAM files from dorado basecaller contain unaligned raw base calls; a mapped rate of 0% is completely normal and should not be flagged as an issue.
- Basecall quality should be evaluated primarily by avg_quality and read count.

Report requirements:
1. Start with a one-sentence summary (success/failure, overall quality).
2. List key statistics per file (total_reads, avg_quality, avg_read_length, etc.).
3. Provide biological interpretation based on functional analysis results.
4. If there are genuine issues or warnings (e.g. low Q-score, insufficient reads), list them separately with recommendations.
5. Use Markdown format. Do not include internal system logs or raw error fields."""
    else:
        report_prompt = f"""你是生物信息学专家，请根据以下分析结果生成一份专业的中文报告。

【执行工具】：{tool_desc}
【工具原始输出（摘要）】：
{raw_output_text}

【文件统计指标】：
{stats_json}

【功能分析结论】：
{func_json}

【背景知识】：
- dorado basecaller 输出的 BAM 是未比对的原始碱基序列，mapped rate 为 0% 是完全正常的，不应作为问题报出。
- basecall 质量评估应以平均 Q 值（avg_quality）和 reads 数量为核心指标。

报告要求：
1. 先给出一句话总结（任务是否成功、整体质量）；
2. 按文件逐一列出关键统计数字（total_reads、avg_quality、avg_read_length 等）；
3. 结合功能分析结论给出生物学解读；
4. 如有真实问题或警告（如 Q 值过低、reads 数量不足），单独列出并给出建议；
5. 语言简洁、专业，使用 Markdown 格式。不要把内部系统日志或错误字段写入报告。"""

    try:
        raw_report = llm.invoke(report_prompt)
        report     = raw_report if isinstance(raw_report, str) else raw_report.content
        report     = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()
    except Exception as e:
        ui_print(f"[Summarizer] Report generation failed: {e}")
        report = (
            f"### ✅ Execution Summary\n\nTools completed, but report generation failed: {e}"
            if lang == "en_US" else
            f"### ✅ 任务执行总结\n\n工具执行完成，但报告生成失败：{e}"
        )

    # ── 步骤 6：画图（在 run_dir 内生成 PNG）────────────────────────────────
    plot_paths_in_run: list[str] = []
    if run_dir and os.path.isdir(run_dir):
        try:
            from tools.analyzers.file.bam_plotter import generate_bam_plots
            _plotter_available = True
        except ImportError as e:
            ui_print(f"[Summarizer] 画图模块不可用（{e}），跳过图表生成")
            _plotter_available = False

        if _plotter_available:
            for stats in file_stats_map.values():
                if stats.get("type") == "bam" and "error" not in stats:
                    try:
                        ui_print("[Summarizer] 正在生成 BAM 图表...")
                        generated = generate_bam_plots(stats, run_dir)
                        plot_paths_in_run.extend(generated)
                        ui_print(f"[Summarizer] 生成图表: {[os.path.basename(p) for p in generated]}")
                    except Exception as e:
                        ui_print(f"[Summarizer] 图表生成失败: {e}")

    # ── 步骤 7：保存分析结果 JSON，将整个 run_dir 归档到 session_dir 下 ─────
    session_dir   = get_session_dir()
    archived_images: list[str] = []

    if run_dir and os.path.isdir(run_dir) and session_dir and os.path.isdir(session_dir):
        # 保存分析结果 JSON 到 run_dir 内
        analysis_result = {
            "file_stats":         file_stats_map,
            "functional_results": functional_results,
        }
        json_path = os.path.join(run_dir, "analysis.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            ui_print(f"[Summarizer] 分析结果 JSON 写入失败: {e}")

        # 收集 run_dir 内的图片路径（移动后更新）
        for entry in os.scandir(run_dir):
            if entry.is_file() and entry.name.endswith(".png"):
                archived_images.append(os.path.join(run_dir, entry.name))

        # run_dir 本身已是 session_dir 的子目录（get_or_create_run_dir 创建在 session_dir 下）
        # 直接保留即可，无需额外移动；run_dir 不删除，作为本次运行的持久存档
        ui_print(f"[Summarizer] 运行结果已归档至: {os.path.basename(run_dir)}")
    elif run_dir:
        ui_print("[Summarizer] 警告：run_dir 或 session_dir 无效，跳过文件归档")

    state["final_answer"]    = report
    state["analysis_images"] = archived_images
    ui_print("[Summarizer] 报告生成完成")
    return state

def handle_irrelevant_request_node(state: AgentState) -> AgentState:
    ui_print("\n[Irrelevant] Generating off-topic reply...")
    lang = get_lang()
    state["final_answer"] = (
        "Sorry, I specialise in nanopore sequencing and modification detection tasks and cannot help with that."
        if lang == "en_US" else
        "抱歉，我专注于纳米孔测序和修饰检测相关的任务，无法为您提供该信息。"
    )
    ui_print(f'\n[LLM Answer] {state["final_answer"]}')
    return state


def finish_session_node(state: AgentState) -> AgentState:
    ui_print(f"\n[End] 本次会话结束")
    return state

