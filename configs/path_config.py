import os

# 获取当前文件（rag_retriever.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 static 目录在 rag_retriever.py 的上一级目录
PROJECT_ROOT = os.path.dirname(current_dir)

DATA_PATH = {
    "dorado": {
        'base_data_dir': "~/agent_data",  # 基础数据路径
        'dorado_models': "~/tools/dorado_model/"
    },
    "samtools": {
        'base_data_dir': "~/agent_data"
    },
    "nextflow": {
        "base_data_dir": "~/agent_data",
        "work_dir": "~/agent_data/nextflow_work",
        "nfcore_home": "~/agent_data/.nextflow"
    }
}

IMAGE_PATH = {
    'image_store': "~/singularity_image",  # 镜像存放路径
}

OTHER_PATH = {
    "db_dir": os.path.join(PROJECT_ROOT, "static/vector_db_cache"),
    "graph_image": os.path.join(PROJECT_ROOT, "static/langgraph_flow.txt"),
}