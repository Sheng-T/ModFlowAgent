# runtime/env_wrapper.py
import os

from configs import IMAGE_PATH, TOOLS_IMAGE, DATA_PATH


class EnvWrapper:
    def __init__(self):
        # 基础配置：这里你可以根据实际情况修改
        self.image_store = IMAGE_PATH['image_store']  # 镜像存放路径


    def wrap_command(self, tool_name: str, raw_cmd: str, is_workflow: bool = False) -> str:
        if is_workflow:
            return self._wrap_workflow_command(raw_cmd)
        return self._wrap_tool_chain_command(tool_name, raw_cmd)

    def _wrap_tool_chain_command(self, tool_name: str, raw_cmd: str):
        """将原始命令封装进 Singularity"""
        image_name = TOOLS_IMAGE.get(tool_name)
        if not image_name:
            print(f'[Wrapper] 未找到镜像: {tool_name} → fallback 本地执行')
            return raw_cmd  # 如果没找到镜像，尝试直接运行

        image_path = os.path.join(self.image_store, tool_name, image_name)

        binds = ''
        for path in DATA_PATH.get(tool_name, {}).values():
            abs_path = os.path.expanduser(path)
            binds += f"--bind {abs_path}:{abs_path} "

        # 封装逻辑：
        # --nv: 开启 GPU 支持 (dorado 必备)
        # --bind: 挂载数据目录，确保容器内外路径一致
        wrapped = (
                f"LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/nvidia/lib:$LD_LIBRARY_PATH "
                f"singularity exec --nv "
                + binds +
                f"{image_path} /bin/bash -c \"{raw_cmd}\""
        )
        return wrapped

    def _wrap_workflow_command(self, raw_cmd: str):
        """
        因为宿主机已安装 Nextflow，直接返回原始命令。
        Nextflow 会通过 -profile singularity 内部处理容器逻辑。
        """
        # 无需封装，直接返回
        return raw_cmd
