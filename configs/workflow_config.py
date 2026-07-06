# Set true on air-gapped servers where Nextflow plugins must be pre-cached
NEXTFLOW_OFFLINE = True

DEFAULT_WORKFLOW_ARGS = {
    "profile": "singularity",
}


MAX_WORKFLOW_RESOURCES = {
    "max_cpus":   None,       # None → auto-detect
    "max_memory": "30.GB",
    "max_time":   "72.h",
}


REQUIRED_FIELDS = ["pipeline", "input", "outdir"]

# Auto-generated from static/workflows/<name>/<name>_manifest.json
def _build_pipeline_lists():
    try:
        from configs.rag_config import WORKFLOW_MANIFESTS
    except ImportError:
        return [], [], []
    supported, nfcore_descs, local_descs = [], [], []
    for name, m in WORKFLOW_MANIFESTS.items():
        wf_type = m.get("type", "")
        entry = {
            "name": name,
            "short_description": m.get("short_description", ""),
            "description": m.get("description", ""),
            "input": m.get("input", ""),
        }
        if wf_type == "nfcore":
            supported.append(name)
            nfcore_descs.append(entry)
        elif wf_type == "local":
            local_descs.append(entry)
    return supported, nfcore_descs, local_descs

SUPPORTED_PIPELINES, PIPELINE_DESCRIPTIONS, LOCAL_PIPELINE_DESCRIPTIONS = _build_pipeline_lists()


def pipeline_exists(name: str) -> bool:
    try:
        from configs.rag_config import WORKFLOW_PIPELINE_DOCS
        return str(name).lower() in WORKFLOW_PIPELINE_DOCS
    except Exception:
        return str(name).lower() in SUPPORTED_PIPELINES




