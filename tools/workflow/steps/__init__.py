"""
Deterministic step builders for local workflows.

Each workflow that has a fixed, known command sequence gets a file here named
after its registry `spec.name` (e.g. `ont_rna.py`, `ont_dna.py`).

The file must export:

    def build_step_command(
        step: str,               # step name from spec.steps (e.g. "dorado_basecaller")
        prereq: dict,            # local_prereq_params from state
        data_path: dict,         # tool data_path config
        step_dir: str,           # this step's dedicated output directory
        all_step_dirs: dict,     # {step_name: abs_path} for ALL steps in the workflow
    ) -> tuple[str, str] | None:
        ...

Return value:
    (base_tool_name, raw_shell_command)   — command to run, tool name for Singularity lookup
    None                                  — skip this step entirely

If no file exists for a workflow, params.py falls back to LLM-generated parameters.
"""
import importlib.util
import os

_STEPS_DIR = os.path.dirname(__file__)


def get_step_builder(workflow_name: str):
    """
    Return the step-builder module for *workflow_name*, or None if not found.
    The returned module has a callable `build_step_command`.
    """
    path = os.path.join(_STEPS_DIR, f"{workflow_name}.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location(f"wf_steps_{workflow_name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod if hasattr(mod, "build_step_command") else None
