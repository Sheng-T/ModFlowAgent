import os

# 获取当前文件（rag_retriever.py）的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 static 目录在 rag_retriever.py 的上一级目录
PROJECT_ROOT = os.path.dirname(current_dir)

USER_HOME = os.environ.get("HOME") or os.path.expanduser("~")

DATA_PATH = {
    "dorado": {
        'base_data_dir': f"{USER_HOME}/agent_data",
        'dorado_models': f"{USER_HOME}/tools/dorado_model/",
        # Pod5 sampling rate: 4000 for older R10.4.1 data, 5000 for newer; 0 = auto (pick latest)
        'sample_rate': 4000,
    },
    "samtools": {
        'base_data_dir': f"{USER_HOME}/agent_data"
    },
    "modkit": {
        'base_data_dir': f"{USER_HOME}/agent_data"
    },
    "fastqc": {
        'base_data_dir': f"{USER_HOME}/agent_data"
    },
    "workflow": {
        "base_data_dir": f"{USER_HOME}/agent_data",
        "work_dir": f"{USER_HOME}/agent_data/nextflow_work",
        "nfcore_home": f"{USER_HOME}/agent_data/.nextflow",
        # Directory containing local nextflow pipelines (e.g. agent_workflow/).
        # Each subdirectory here is treated as a pipeline name.
        # Leave empty to use PROJECT_ROOT/agent_workflow as the default.
        "pipeline_dir": f"{USER_HOME}/agent_workflow/",
    }
}

IMAGE_PATH = {
    'image_store': f"{USER_HOME}/singularity_image",  # 镜像存放路径
}

OTHER_PATH = {
    "db_dir": os.path.join(PROJECT_ROOT, "static/vector_db_cache"),
    "graph_image": os.path.join(PROJECT_ROOT, "static/langgraph_flow.txt"),
    # 持久化存储
    "checkpoint_db": os.path.join(PROJECT_ROOT, "static/checkpoints/agent.db"),
    "session_db": os.path.join(PROJECT_ROOT, "static/sessions/sessions.db"),
    # 用户上传文件根目录（子目录按 uid/session_id 隔离）
    "user_data_root": os.path.join(PROJECT_ROOT, "static/user_data"),
}

# 单用户最大存储配额（字节），默认 10 GB
USER_QUOTA_BYTES = 10 * 1024 * 1024 * 1024