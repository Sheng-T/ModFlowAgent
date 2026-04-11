"""
轻量 i18n 工具。

用法:
    from utils.i18n import _
    st.button(_("登录"))

翻译策略:
  - zh_CN 是源语言，直接返回原字符串（零开销）
  - 其他语言在 TRANSLATIONS[lang] 中查找；缺失 key 则 fallback 到原字符串
  - 当前语言从 st.session_state.lang 读取，缺失时用 DEFAULT_LANG
"""

from configs.i18n_config import DEFAULT_LANG

# ── 翻译表 ────────────────────────────────────────────────────────────────────
# key = zh_CN 原始字符串，value = 目标语言字符串
# 添加新语言：在 TRANSLATIONS 里增加一个 lang key，填入对应翻译即可。

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en_US": {
        # ── 登录 ──────────────────────────────────────────────────────────
        "请输入用户名以继续":          "Enter your username to continue",
        "用户名":                      "Username",
        "例如：alice":                 "e.g. alice",
        "登录":                        "Login",

        # ── 侧边栏 ────────────────────────────────────────────────────────
        "切换用户":                    "Switch User",
        "➕ 新建会话":                 "➕ New Session",
        "会话列表":                    "Sessions",
        "条消息":                      "messages",
        "语言":                        "Language",
        "🧰 支持的工具与流水线":        "🧰 Supported Tools & Pipelines",
        "单步工具":                    "Tools",
        "分析流水线":                  "Pipelines",
        "📁 文件管理":                 "📁 File Management",
        "上传文件到当前会话":           "Upload files to current session",
        "个文件":                      "files",
        "🗑 清空当前会话文件":          "🗑 Clear session files",
        "各会话占用":                  "Storage by session",
        "当前":                        "current",

        # ── 主区域 ────────────────────────────────────────────────────────
        "🧬 Bio-Agent 智能分析平台":   "🧬 Bio-Agent Analytics Platform",
        "正在加载模型...":             "Loading model...",
        "请输入你的分析指令...":       "Enter your analysis instruction...",

        # ── 模式选择 ──────────────────────────────────────────────────────
        "你的输入":                    "Your input",
        "请选择处理方式：":            "Select processing mode:",
        "💬 对话问答":                 "💬 Chat Q&A",
        "🔧 工具调用":                 "🔧 Tool Call",
        "🧬 流水线":                   "🧬 Pipeline",
        "🤖 自动判断":                 "🤖 Auto Detect",

        # ── 状态标签 ──────────────────────────────────────────────────────
        "🔄 Agent 执行中...":          "🔄 Agent running...",
        "⏸️ 等待你的确认":            "⏸️ Awaiting confirmation",
        "✅ 执行完成":                 "✅ Completed",
        "🔄 继续执行...":              "🔄 Resuming...",

        # ── 审查确认 ──────────────────────────────────────────────────────
        "📋 待执行命令，请确认":       "📋 Pending commands, please confirm",
        "步骤":                        "Step",
        "命令列表为空，请检查参数生成是否正常": "Command list is empty, check parameter generation",
        "🔧 修改意见（提交修改时填写）":        "🔧 Revision notes (fill when submitting)",
        "✅ 确认执行":                 "✅ Confirm & Execute",
        "❌ 取消任务":                 "❌ Cancel",
        "💬 提交修改":                 "💬 Submit Revision",
        "请先填写修改意见":            "Please fill in revision notes first",

        # ── 通用 ──────────────────────────────────────────────────────────
        "🧠 查看思考过程":             "🧠 View thinking process",
        "✅ 任务处理完成":             "✅ Task completed",
        "会话":                        "Session",
    }
}


def _(text: str) -> str:
    """翻译函数。zh_CN 直接原路返回；其他语言查字典，缺失则 fallback 原文。"""
    try:
        import streamlit as st
        lang = st.session_state.get("lang", DEFAULT_LANG)
    except Exception:
        lang = DEFAULT_LANG

    if lang == "zh_CN" or lang not in TRANSLATIONS:
        return text

    return TRANSLATIONS[lang].get(text, text)
