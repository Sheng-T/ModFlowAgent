# Benchmark & Ablation

Three environment variables independently disable ModFlowAgent components:

| Variable | Effect |
|---|---|
| ABLATION_NO_CONTROLLER=1 | Bypass staged workflow controller |
| ABLATION_NO_VALIDATION=1 | Disable validation gates |
| ABLATION_NO_RAG=1 | Disable RAG grounding |

## Benchmark Results

| Evaluation | Cases | Score |
|---|---|---|
| Full ModFlowAgent | 60 | 60/60 |
| Direct LLM (Claude Sonnet 4.6) | 20 | 15.5/20 |
| ModFlowAgent (same 20 cases) | 20 | 20/20 |
| w/o structured controller | 20 | 9/20 |
| w/o validation | 20 | 18/20 |
| w/o RAG grounding | 20 | 18/20 |
