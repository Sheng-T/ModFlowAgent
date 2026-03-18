import json
import os

# 获取当前文件（rag_retriever.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 static 目录在 rag_retriever.py 的上一级目录
project_root = os.path.dirname(current_dir)

# -------------------------------------------------------------------------
LLM_SOURCE = "huggingface"
LLM_NAME = "qwen3_14B"
# LLM_NAME = "gemini_model"

gemini_api = ""

llm_model_path = {
    "qwen3_0_6B": "/ni_data/users/shengtao/model/qwen3-0.6b/models--Qwen--Qwen3-0.6B/snapshots/6130ef31402718485ca4d80a6234f70d9a4cf362/",
    "qwen3_1_7B": "/ni_data/users/shengtao/model/qwen3-1.7b-ab/models--huihui-ai--Huihui-Qwen3-1.7B-abliterated-v2/snapshots/4462327af009cd482a6b308b67ec9b3a6eeb006a/",
    "qwen3_8B": "/ni_data/users/shengtao/model/qwen3-8b",
    "qwen3_14B": "/ni_data/users/shengtao/model/qwen3-14b/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18/",
    "qwen35_27B": "/ni_data/users/shengtao/model/qwen3.5-27B/models--Qwen--Qwen3.5-27B/snapshots/b7ca741b86de18df552fd2cc952861e04621a4bd/",
    "gemini_model": gemini_api,
    "embedding": "/ni_data/users/shengtao/model/all-MiniLM-L6-v2",
    "reranker": "/ni_data/users/shengtao/model/bge-reranker-base/models--BAAI--bge-reranker-base/snapshots/2cfc18c9415c912f9d8155881c133215df768a70/",
}
# -------------------------------------------------------------------------

other_path = {
    "db_dir": os.path.join(project_root, "static/vector_db_cache"),
    "graph_image": os.path.join(project_root, "static/langgraph_flow.txt"),
}

llm_args = {
    'device': 'auto',
}

embedding_args = {
    'device': 'cpu',
}


# -------------------------------------------------------------------------

def load_tool_config(file_name):
    # 获取当前文件所在目录，确保路径正确
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "tool_configs", file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


TOOL_LIST = ['dorado', 'samtools']

TOOL_DESCIPTION = [
    {
        "name": "dorado",
        "description": "Dorado is a high-performance, GPU-accelerated basecalling engine developed by Oxford Nanopore "
                       "Technologies that employs sophisticated deep learning architectures to transform raw ionic current "
                       "signals into high-fidelity nucleotide sequences while enabling the concurrent, real-time detection "
                       "of diverse epigenetic modifications (such as $m^6A$ and $5mC$).",
    },
    {
        "name": "samtools",
        "description": "Samtools serves as the definitive toolkit for the rapid manipulation and statistical analysis "
                       "of high-throughput sequencing data, offering a comprehensive array of subcommands for "
                       "coordinate-based sorting, indexing, format interconversion, and complex filtering of alignment "
                       "records stored in SAM, BAM, and CRAM specifications.",
    },
]

TOOL_ARGS = {
    "dorado": load_tool_config(os.path.join(project_root, "static/dorado/dorado_args.json")),
    "samtools": load_tool_config(os.path.join(project_root, "static/samtools/samtools_args.json")),
}

# 维护一个文档映射表
TOOLS_DOC = {
    "dorado": os.path.join(project_root, "static/dorado/dorado_doc.md"),
    "samtools": os.path.join(project_root, "static/samtools/samtools_doc.md"),
}

TOOLS_IMAGE = {
    "dorado": "dorado_latest.sif",
    "samtools": "samtools_1.16.1.sif",
}

# -------------------------------------------------------------------------

AGENT_PATH = {
    'image_store': "~/singularity_images",  # 镜像存放路径
}

DATA_PATH = {
    "dorado": {
        'base_data_dir': "~/agent_data",  # 基础数据路径
        'dorado_models': "~/tools/dorado_model/"
    },
    "samtools": {
        'base_data_dir': "~/agent_data"
    }
}
