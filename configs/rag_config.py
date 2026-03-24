import os

from configs.path_config import PROJECT_ROOT

TOOLS_DOC = {
    "dorado": os.path.join(PROJECT_ROOT, "static/dorado/dorado_doc.md"),
    "samtools": os.path.join(PROJECT_ROOT, "static/samtools/samtools_doc.md"),
    "nextflow": os.path.join(PROJECT_ROOT, "static/nfcore/nfcore_doc.md"),
}

NFCORE_RAG_INSTANCE = None

RAG_INSTANCES = {}
