# runtime/env_wrapper.py
import atexit
import os
import shlex
import stat
import tempfile

from configs import IMAGE_PATH, DATA_PATH, TOOL_EXEC_ENV, USER_HOME
from configs.app_config import APP_SNAKE
from utils.runner_utils import _find_dorado_lib_path_in_image

# Track temp scripts created this process so they can be cleaned up
_TEMP_SCRIPTS: list[str] = []


def cleanup_temp_scripts():
    """Remove all temp script files created by _wrap_with_exec_env."""
    for path in _TEMP_SCRIPTS:
        try:
            os.unlink(path)
        except OSError:
            pass
    _TEMP_SCRIPTS.clear()


atexit.register(cleanup_temp_scripts)


class EnvWrapper:
    def __init__(self):
        self.image_store = IMAGE_PATH['image_store']

    def _wrap_with_exec_env(self, raw_cmd: str, cwd: str = "") -> str:
        """
        Wrap raw_cmd with the configured TOOL_EXEC_ENV when no Singularity image
        is available.  Returns raw_cmd unchanged when TOOL_EXEC_ENV is None.
        cwd: if provided, the script will cd into this directory before running.
        """
        if not TOOL_EXEC_ENV:
            return raw_cmd

        exec_type = TOOL_EXEC_ENV.get("type", "")

        if exec_type == "conda":
            env_name = TOOL_EXEC_ENV.get("env_name", "")
            if not env_name:
                print("[Wrapper] TOOL_EXEC_ENV type=conda but env_name is empty — running in current env")
                return raw_cmd

            # Write command to a temp script to avoid all shell quoting issues.
            conda_base = os.popen("conda info --base").read().strip()
            script_dir = USER_HOME
            cd_line = f"cd {shlex.quote(cwd)}" if cwd else ""
            tmp = tempfile.NamedTemporaryFile(
                mode='w', suffix='.sh', delete=False, prefix=f'{APP_SNAKE}_',
                dir=script_dir,
            )
            tmp.write(f"""#!/bin/bash
source {conda_base}/etc/profile.d/conda.sh
conda activate {env_name}
{cd_line}
{raw_cmd}
""")
            tmp.close()
            os.chmod(tmp.name, stat.S_IRWXU)
            _TEMP_SCRIPTS.append(tmp.name)
            print(f"[Wrapper] conda env '{env_name}', cwd='{cwd}', script={tmp.name}")
            return f"bash {tmp.name}"

        if exec_type == "script":
            script_path = TOOL_EXEC_ENV.get("script_path", "")
            if not script_path or not os.path.isfile(script_path):
                print(f"[Wrapper] TOOL_EXEC_ENV type=script but script_path '{script_path}' not found — running in current env")
                return raw_cmd
            # The script receives the full command string as its first argument ($1).
            escaped = raw_cmd.replace("'", "'\\''")
            wrapped = f"bash {shlex.quote(script_path)} '{escaped}'"
            print(f"[Wrapper] script wrapper → {wrapped}")
            return wrapped

        print(f"[Wrapper] Unknown TOOL_EXEC_ENV type '{exec_type}' — running in current env")
        return raw_cmd


    def wrap_command(self, tool_name: str, raw_cmd: str,
                     is_workflow: bool = False, cwd: str = "") -> str:
        if is_workflow:
            return self._wrap_workflow_command(raw_cmd, cwd=cwd)
        return self._wrap_tool_chain_command(tool_name, raw_cmd, cwd=cwd)

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

    def _wrap_tool_chain_command(self, tool_name: str, raw_cmd: str, cwd: str = ""):
        """Wrap command in Singularity if an image exists, otherwise use TOOL_EXEC_ENV or current env."""
        image_path = self._resolve_image_path(tool_name)
        if not image_path:
            print(f'[Wrapper] No image found for {tool_name} — using configured exec env')
            return self._wrap_with_exec_env(raw_cmd, cwd=cwd)


        extra_lib = _find_dorado_lib_path_in_image(image_path) if tool_name == "dorado" else ""

        ld_parts = [p for p in [extra_lib, "/usr/local/nvidia/lib64", "/usr/local/nvidia/lib"] if p]
        ld_library_path = ":".join(ld_parts)

        # 收集所有需要 bind 的路径
        bind_paths = set()
        
        # 1. 添加 DATA_PATH 中配置的路径（跳过非字符串值，如 sample_rate）
        for path in DATA_PATH.get(tool_name, {}).values():
            if not isinstance(path, str):
                continue
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
        
        # 提取命令中所有绝对路径（带引号或裸路径），跳过标准系统目录
        _SKIP_PREFIXES = ('/usr', '/bin', '/lib', '/etc', '/proc', '/sys',
                          '/dev', '/run', '/tmp', '/var')
        _quoted  = re.findall(r'"(/[^"]+)"', raw_cmd)
        _unquoted = re.findall(r'(?<!\w)(/[^\s>|"\'\\]+)', raw_cmd)
        for path in _quoted + _unquoted:
            path = path.rstrip('.,;)')
            if any(path.startswith(p) for p in _SKIP_PREFIXES):
                continue
            check_path = path
            while check_path and check_path != '/':
                if os.path.islink(check_path):
                    # 绑定软链接所在目录，并递归解析目标路径也一起绑定
                    parent = os.path.dirname(check_path)
                    if parent:
                        bind_paths.add(parent)
                    real = os.path.realpath(check_path)
                    if not any(real.startswith(p) for p in _SKIP_PREFIXES):
                        if os.path.isfile(real):
                            bind_paths.add(os.path.dirname(real))
                        elif os.path.isdir(real):
                            bind_paths.add(real)
                    break
                elif os.path.isdir(check_path):
                    bind_paths.add(check_path)
                    break
                elif os.path.isfile(check_path):
                    bind_paths.add(os.path.dirname(check_path))
                    break
                check_path = os.path.dirname(check_path)
        
        # 构建 bind 参数
        binds = ''
        for bind_path in sorted(bind_paths):
            binds += f"--bind {bind_path}:{bind_path} "

        # Write the inner command to a temp script so no shell quoting is needed
        # when embedding it into the singularity exec call.  This avoids the
        # incomplete escaping problem (backticks, $(), etc.) that arises when
        # splicing raw_cmd into a -c "..." string.
        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.sh', delete=False, prefix=f'{APP_SNAKE}_sing_',
            dir=USER_HOME,
        )
        tmp.write(f"""#!/bin/bash
export LD_LIBRARY_PATH={ld_library_path}:$LD_LIBRARY_PATH
{raw_cmd}
""")
        tmp.close()
        os.chmod(tmp.name, stat.S_IRWXU)
        _TEMP_SCRIPTS.append(tmp.name)

        wrapped = (
            f"singularity exec --nv "
            f"--bind /usr/local/nvidia:/usr/local/nvidia "
            + binds
            + f"{shlex.quote(image_path)} bash {shlex.quote(tmp.name)}"
        )
        return wrapped

    def _wrap_workflow_command(self, raw_cmd: str, cwd: str = "") -> str:
        """
        Wrap a workflow (Nextflow) command with TOOL_EXEC_ENV if configured.
        cwd is passed into the script as an explicit cd line.
        """
        return self._wrap_with_exec_env(raw_cmd, cwd=cwd)
