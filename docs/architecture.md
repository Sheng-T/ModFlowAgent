# Architecture

## Overview

ModFlowAgent is implemented as a LangGraph-based state graph with controlled stages for intent routing, workflow planning, prerequisite validation, parameter and command generation, user confirmation, execution, and result summarization.

## System Architecture

```
User Input
   │
   ▼
[router] ── Intent Classification ─────────────────────────┐
   │                                                        │
   ▼ Tool / Workflow                             ▼ QA ▼ Irrelevant
[tools_selector]                              [llm_answer]  [irrelevant]
   │
   ├── Single tool ──▶ [rag] ──▶ [planner] ──▶ [param_generator]
   │
   └── Workflow ──▶ [planner]
                       │
                       ├── Auto-detected ───────────────────────┐
                       │                                         │
                       └── Ambiguous ──▶ [human_workflow_selector]
                                              │
                  ┌────────────────────────────┘
                  ▼
        workflow_type == "nfcore"     workflow_type == "local"
                  │                              │
                  ▼                              ▼
           [rag_pipeline]              [local_prereq_generator]
                  │                              │
          [prereq_generator]          [human_local_prereq_reviewer]
                  │                              │
                  └──────────┬───────────────────┘
                             ▼
                    [param_generator]
                             │
                    [human_reviewer]
                             │
                       [executor]
                  ┌──────────┴──────────┐
                  ▼                     ▼
            [summarizer] → END     [param_generator] (retry)
```

## Interrupt Nodes

| Node | Condition | How it pauses |
|---|---|---|
| `human_workflow_selector` | LLM cannot auto-select a workflow | `interrupt_before` |
| `human_prereq_reviewer` | nfcore samplesheet generated and validated | `interrupt_before` |
| `human_local_prereq_reviewer` | local workflow parameters generated | `interrupt_before` |
| `human_reviewer` | All commands ready for review | `interrupt_after` |

## Design Notes

- `workflow_type: str` — Values: `"nfcore"`, `"local"`, `""`, serves as the sole routing signal for workflow branching.
- Manifest auto-discovery — `rag_config.py` scans `static/tools/` and `static/workflows/` at startup. Each pipeline has a `<name>_manifest.json` declaring type, description, input format, and tools used.
- `WorkflowSpec` registry — `tools/workflow/registry.py` is the single source of truth for step definitions, display names, and recommendation criteria.
- Deterministic step builders — `tools/workflow/local/{name}.py` generates precise shell commands without LLM invocation.
- `model_map.py` — Maps `(molecule, modification_type)` to dorado model pairs + modkit flags.
- Per-workflow prompt modules — `agent_graph/prompts/workflows/{name}/` can hold `prereq_prompt.py`, `params_prompt.py`, `qa_rules.py`, dynamically discovered via `importlib`.
- `run_dir` isolation — Each run creates an isolated directory under `session_dir/run_{id}_{timestamp}/`.
- Background file server — `utils/file_server.py` serves large files via HTTP, avoiding Streamlit WebSocket MemoryError.
- `pending_commands` reuse — The review node determines all paths (including timestamps) in one pass; the executor reuses them directly.
