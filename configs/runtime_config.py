
llm_args = {
    'device': 'cuda:3',
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

