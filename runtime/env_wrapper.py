# runtime/env_wrapper.py
import os

from configs import IMAGE_PATH, DATA_PATH


class EnvWrapper:
    def __init__(self):
        # 基础配置：这里你可以根据实际情况修改
        self.image_store = IMAGE_PATH['image_store']  # 镜像存放路径


    def wrap_command(self, tool_name: str, raw_cmd: str, is_workflow: bool = False) -> str:
        if is_workflow:
            return self._wrap_workflow_command(raw_cmd)
        return self._wrap_tool_chain_command(tool_name, raw_cmd)

    def _resolve_image_path(self, tool_name: str) -> str | None:
        """
        扫描 {image_store}/{tool_name}/ 目录，
        找到第一个 .img 或 .sif 文件（优先 .img）。
        目录不存在或没有镜像文件时返回 None。
        """
        tool_dir = os.path.join(os.path.expanduser(self.image_store), tool_name)
        if not os.path.isdir(tool_dir):
            return None

        img_files = [f for f in os.listdir(tool_dir) if f.endswith((".img", ".sif"))]
        if not img_files:
            return None

        # 优先选 .img，相同格式按文件名排序取第一个
        img_files.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
        return os.path.join(tool_dir, img_files[0])

    def _wrap_tool_chain_command(self, tool_name: str, raw_cmd: str):
        """将原始命令封装进 Singularity"""
        image_path = self._resolve_image_path(tool_name)
        if not image_path:
            print(f'[Wrapper] 未找到镜像配置: {tool_name} → fallback 本地执行')
            return raw_cmd

        # 收集所有需要 bind 的路径
        bind_paths = set()
        
        # 1. 添加 DATA_PATH 中配置的路径
        for path in DATA_PATH.get(tool_name, {}).values():
            abs_path = os.path.expanduser(path)
            if os.path.isdir(abs_path):
                bind_paths.add(abs_path)
        
        # 2. 从命令中自动提取输出路径（智能识别）
        # 提取常见输出指示：> 重定向、-o/--output 参数、等
        import re
        
        # 提取 > 或 >> 后面的文件路径
        redirect_matches = re.findall(r'[>|]\s*(/[^\s>|]+)', raw_cmd)
        for path in redirect_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)
        
        # 提取 -o 或 --output 后面的路径
        output_matches = re.findall(r'(?:-o|--output)\s+(/[^\s-][^\s]*)', raw_cmd)
        for path in output_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)
        
        # 提取命令中所有的绝对路径（以 /home 开头的），为其所在目录添加 bind
        all_paths = re.findall(r'/home/[^\s>|]+', raw_cmd)
        for path in all_paths:
            # 尝试找到有效的目录
            check_path = path
            while check_path and check_path != '/':
                if os.path.isdir(check_path):
                    bind_paths.add(check_path)
                    break
                elif os.path.isfile(check_path):
                    parent_dir = os.path.dirname(check_path)
                    if parent_dir:
                        bind_paths.add(parent_dir)
                    break
                check_path = os.path.dirname(check_path)
        
        # 构建 bind 参数
        binds = ''
        for bind_path in sorted(bind_paths):
            binds += f"--bind {bind_path}:{bind_path} "

        # 封装逻辑：
        # --nv: 开启 GPU 支持 (dorado 必备)
        # --bind: 挂载数据目录，确保容器内外路径一致
        # wrapped = (
        #         f"LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/nvidia/lib:$LD_LIBRARY_PATH "
        #         f"singularity exec --nv "
        #         f"--bind /usr/local/nvidia:/usr/local/nvidia "
        #         + binds +
        #         f"{image_path} /bin/bash -c \"{raw_cmd}\""
        # )
        wrapped = (
                f"singularity exec --nv "
                f"--bind /usr/local/nvidia:/usr/local/nvidia "
                + binds +
                f"{image_path} /bin/bash -c \""
                f"export LD_LIBRARY_PATH=/usr/local/nvidia/lib64:/usr/local/nvidia/lib:\\$LD_LIBRARY_PATH && "
                f"{raw_cmd}\""
        )
        return wrapped

    def _wrap_workflow_command(self, raw_cmd: str):
        """
        因为宿主机已安装 Nextflow，直接返回原始命令。
        Nextflow 会通过 -profile singularity 内部处理容器逻辑。
        """
        # 无需封装，直接返回
        return raw_cmd
