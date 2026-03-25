import json
import os


# utils/config_utils.py
def load_tool_config(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            print(f"[Config] 警告: {path} 是空文件，跳过")
            return {}
        return json.loads(content)