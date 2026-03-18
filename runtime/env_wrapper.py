# runtime/env_wrapper.py
import os

from utils.common_utils import AGENT_PATH, TOOLS_IMAGE, DATA_PATH


class EnvWrapper:
    def __init__(self):
        # 基础配置：这里你可以根据实际情况修改
        self.image_store = AGENT_PATH['image_store']  # 镜像存放路径


    def wrap_command(self, tool_name: str, raw_cmd: str) -> str:
        """将原始命令封装进 Singularity"""
        image_name = TOOLS_IMAGE.get(tool_name)
        if not image_name:
            return raw_cmd  # 如果没找到镜像，尝试直接运行

        image_path = os.path.join(self.image_store, image_name)

        binds = ''
        for data_path in DATA_PATH[tool_name]:
            binds += f"--bind {data_path}:{data_path} "

        # 封装逻辑：
        # --nv: 开启 GPU 支持 (dorado 必备)
        # --bind: 挂载数据目录，确保容器内外路径一致
        wrapped = (
            f"singularity exec --nv "
            f"--env LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/nvidia/lib:$LD_LIBRARY_PATH " +
            binds +
            f"{image_path} /bin/bash -c '{raw_cmd}'"
        )
        return wrapped