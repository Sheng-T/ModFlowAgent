# Developer Guide

## Adding a Local Workflow

1. Create `static/workflows/<name>/<name>_manifest.json`
2. Register in `tools/workflow/registry.py`: `register(WorkflowSpec(...))`
3. Implement step builder: `tools/workflow/local/{name}.py`
4. Add prerequisite form in `static/workflows/workflow_prereqs.json`
5. (Optional) Add per-workflow prompts in `agent_graph/prompts/workflows/{name}/`

## Adding an nf-core Workflow

1. Create manifest in `static/workflows/<name>/`
2. Register `WorkflowSpec` in `tools/workflow/registry.py`
3. Add prerequisite form in `workflow_prereqs.json`
4. Create validator in `tools/workflow/nf/{name}/validator.py`

## Adding a New Tool

1. Add command builder to `tools/toolchain/{tool}/validator.py`
2. Register in `tools/registry.py`: `TOOL_REGISTRY["tool_name"] = my_validator`
3. Add to `configs/tool_config.py`: `TOOL_LIST`
4. Add documentation in `static/tools/{tool}/{tool}_doc.md`
5. (Optional) Add command rules in `static/tools/{tool}/{tool}_rules.md`

## Adding a Modification Type

Edit tool-specific validator files:
1. Add mod model to `RNA_MOD_MODELS` or `DNA_MOD_MODELS`
2. Add flag logic to `get_modkit_flags()` in `tools/toolchain/modkit/validator.py`
3. Add option to `static/workflows/workflow_prereqs.json`

## Per-Workflow QA Hints

Create `agent_graph/prompts/workflows/{name}/qa_rules.py` with `get_qa_hints(lang)`.
The QA node automatically discovers and injects it.
