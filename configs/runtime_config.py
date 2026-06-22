
# Port for the background streaming file-download server (Streamlit port + 1 by default)
FILE_SERVER_PORT = 50028

llm_args = {
    'device': 'cuda:3',
    'max_new_tokens': 4096,
}

embedding_args = {
    'device': 'cpu',
}

# Optional: execution environment for bioinformatics tools.
# When a Singularity image is NOT found for a tool, commands fall back to running
# in the shell. If your agent and your tools live in different conda environments,
# set this to avoid "command not found" errors.
#
# Option A — conda environment:
#   TOOL_EXEC_ENV = {"type": "conda", "env_name": "biotools"}
#   → wraps command as: conda run --no-capture-output -n biotools bash -c "<cmd>"
#
# Option B — shell script prefix (the script receives the command as $1):
#   TOOL_EXEC_ENV = {"type": "script", "script_path": "/home/user/run_in_bioenv.sh"}
#   → wraps command as: bash /home/user/run_in_bioenv.sh "<cmd>"
#
# Leave as None to run in the current Python process environment (default).

TOOL_EXEC_ENV = {"type": "conda", "env_name": "sin"}
# TOOL_EXEC_ENV = None

# Number of CPU threads for bioinformatics tools (samtools, modkit, etc.)
TOOL_THREADS = 16

# SearXNG instance URL for Q&A web search.
# Leave as "" to skip SearXNG and fall back to DuckDuckGo snippets.
# Self-host with one command: docker run -d -p 8080:8080 searxng/searxng
# Then set: SEARXNG_URL = "http://localhost:8080"
SEARXNG_URL = ""

