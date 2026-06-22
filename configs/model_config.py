
# ── Read API settings from secrets.py (gitignored) ────────────────────────────
def _secret(name: str, default=""):
    try:
        import api_keys as _s
        return getattr(_s, name, default) or default
    except ImportError:
        return default

_api_key = _secret("LLM_API_KEY")

# Auto-switch: local GPU when no API key, API mode when key is set.
# To force local model even with a key set, change LLM_SOURCE manually.
LLM_SOURCE = "api"        if _api_key else "huggingface"
LLM_NAME   = "openai_compatible" if _api_key else "qwen3_14B"

gemini_api = ""

# OpenAI-compatible endpoint config — all values read from secrets.py.
# Configure base_url, model, etc. there; never put keys in this file.
# base_url examples:
#   OpenAI:        https://api.openai.com/v1
#   DeepSeek:      https://api.deepseek.com/v1
#   SiliconFlow:   https://api.siliconflow.cn/v1
#   Ollama:        http://localhost:11434/v1
openai_compat_config = {
    "base_url":   _secret("LLM_API_BASE_URL", "https://api.deepseek.com/v1"),
    "api_key":    _api_key,
    "model":      _secret("LLM_API_MODEL",    "deepseek-chat"),
    "max_tokens": _secret("LLM_API_MAX_TOKENS", 8192),
}

llm_model_path = {
    "qwen3_0_6B":  "/path/to/qwen3-0.6b",
    "qwen3_1_7B":  "/path/to/qwen3-1.7b",
    "qwen3_8B":    "/path/to/qwen3-8b",
    "qwen3_14B":   "/path/to/qwen3-14b",
    "qwen35_27B":  "/path/to/qwen3.5-27b",
    "gemini_model": gemini_api,
    "embedding":   "/path/to/embedding-model",
    "reranker":    "/path/to/reranker-model",
}



