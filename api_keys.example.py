# Copy this file to api_keys.py and fill in your keys.
# api_keys.py is gitignored — never commit your real keys.

# LLM API configuration
# When LLM_API_KEY is non-empty, the system automatically switches to API mode
# and the local GPU model is NOT loaded.
LLM_API_KEY      = ""
LLM_API_BASE_URL = "https://api.deepseek.com/v1"   # OpenAI-compatible endpoint
LLM_API_MODEL    = "deepseek-v4-flash"                  # model name on that endpoint
LLM_API_MAX_TOKENS = 1000000

# Tavily Search API (https://app.tavily.com — free 1000 req/month)
# When set, Q&A search uses Tavily instead of the web-crawling fallback.
TAVILY_API_KEY = ""

# SearXNG public instances (tried in order, first success wins).
# Defaults are built into the code — override here only if you want different ones.
# Leave empty list [] to disable SearXNG entirely.
SEARXNG_INSTANCES = []
