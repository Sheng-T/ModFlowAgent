"""
Workflow analyzer registry — maps workflow name → WorkflowAnalyzer instance.
Add a new entry here when adding a new workflow-specific analyzer.
Workflows not listed fall back to the generic MultiQC-only summary.
"""
from tools.analyzers.workflow.methylong import MethylongAnalyzer

WORKFLOW_ANALYZER_REGISTRY: dict = {
    "methylong": MethylongAnalyzer(),
}


def get_workflow_analyzer(workflow_name: str):
    """Return the registered WorkflowAnalyzer, or None for the generic fallback."""
    return WORKFLOW_ANALYZER_REGISTRY.get(workflow_name.lower())
