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


def _pick_script_dir(cwd: str = "") -> str:
    """Prefer the current step/run directory for wrapper scripts; fall back to USER_HOME."""
    if cwd and os.path.isdir(cwd):
        return cwd
    return USER_HOME


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

    _IMAGE_TOOL_ALIASES = {
        "pbjasmine": ["pbjasmine", "jasmine"],
        "pb-cpg-tools": ["pb-cpg-tools", "pb_cpg_tools", "pbcpgtools"],
        "fibertools-rs": ["fibertools-rs", "fibertools"],
        "modkit": ["modkit", "ont-modkit"],
    }

    def _wrap_with_exec_env(self, raw_cmd: str, cwd: str = "", exec_env: dict | None = None) -> str:
        """
        Wrap raw_cmd with the configured TOOL_EXEC_ENV when no Singularity image
        is available.  Returns raw_cmd unchanged when TOOL_EXEC_ENV is None.
        cwd: if provided, the script will cd into this directory before running.
        """
        exec_env = exec_env if exec_env is not None else TOOL_EXEC_ENV
        if not exec_env:
            return raw_cmd

        exec_type = exec_env.get("type", "")

        if exec_type == "conda":
            env_name = exec_env.get("env_name", "")
            if not env_name:
                print("[Wrapper] TOOL_EXEC_ENV type=conda but env_name is empty — running in current env")
                return raw_cmd

            # Write command to a temp script to avoid all shell quoting issues.
            conda_base = os.popen("conda info --base").read().strip()
            script_dir = _pick_script_dir(cwd)
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
            script_path = exec_env.get("script_path", "")
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
                     is_workflow: bool = False, cwd: str = "",
                     runtime_override: dict | None = None) -> str:
        if is_workflow:
            return self._wrap_workflow_command(raw_cmd, cwd=cwd)
        if runtime_override and runtime_override.get("type") == "conda":
            return self._wrap_with_exec_env(raw_cmd, cwd=cwd, exec_env=runtime_override)
        if runtime_override and runtime_override.get("type") == "script":
            return self._wrap_with_exec_env(raw_cmd, cwd=cwd, exec_env=runtime_override)
        if runtime_override and runtime_override.get("type") == "singularity":
            image_path = os.path.expanduser(runtime_override.get("image", ""))
            return self._wrap_singularity_command(tool_name, raw_cmd, image_path, cwd=cwd)
        return self._wrap_tool_chain_command(tool_name, raw_cmd, cwd=cwd)

    def _wrap_singularity_command(self, tool_name: str, raw_cmd: str, image_path: str, cwd: str = ""):
        """Wrap command in a specific Singularity image."""
        if not image_path or not os.path.isfile(image_path):
            return self._wrap_with_exec_env(raw_cmd, cwd=cwd)

        extra_lib = _find_dorado_lib_path_in_image(image_path) if tool_name == "dorado" else ""
        ld_parts = [p for p in [extra_lib, "/usr/local/nvidia/lib64", "/usr/local/nvidia/lib"] if p]
        ld_library_path = ":".join(ld_parts)

        bind_paths = set()
        if cwd and os.path.isdir(cwd):
            bind_paths.add(cwd)

        for path in DATA_PATH.get(tool_name, {}).values():
            if not isinstance(path, str):
                continue
            abs_path = os.path.expanduser(path)
            if os.path.isdir(abs_path):
                bind_paths.add(abs_path)

        import re

        redirect_matches = re.findall(r'[>|]\s*(/[^\s>|]+)', raw_cmd)
        for path in redirect_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)

        output_matches = re.findall(r'(?:-o|--output)\s+(/[^\s-][^\s]*)', raw_cmd)
        for path in output_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)

        _SKIP_PREFIXES = ('/usr', '/bin', '/lib', '/etc', '/proc', '/sys', '/dev', '/run', '/tmp', '/var')
        _quoted = re.findall(r'"(/[^"]+)"', raw_cmd)
        _unquoted = re.findall(r'(?<!\w)(/[^\s>|"\'\\]+)', raw_cmd)
        for path in _quoted + _unquoted:
            path = path.rstrip('.,;)')
            if any(path.startswith(p) for p in _SKIP_PREFIXES):
                continue
            check_path = path
            while check_path and check_path != '/':
                if os.path.islink(check_path):
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

        binds = ''
        for bind_path in sorted(bind_paths):
            binds += f"--bind {bind_path}:{bind_path} "

        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.sh', delete=False, prefix=f'{APP_SNAKE}_sing_',
            dir=_pick_script_dir(cwd),
        )
        tmp.write(f"""#!/bin/bash
export LD_LIBRARY_PATH={ld_library_path}:$LD_LIBRARY_PATH
{f'cd {shlex.quote(cwd)}' if cwd else ''}
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

    def _resolve_image_path(self, tool_name: str) -> str | None:
        base_store = os.path.expanduser(self.image_store)
        aliases = self._IMAGE_TOOL_ALIASES.get(tool_name, [tool_name])

        for alias in aliases:
            tool_dir = os.path.join(base_store, alias)
            if not os.path.isdir(tool_dir):
                continue
            img_files = [f for f in os.listdir(tool_dir) if f.endswith((".img", ".sif"))]
            if not img_files:
                continue
            img_files.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
            return os.path.join(tool_dir, img_files[0])

        methylong_cache = os.path.join(base_store, "workflow", "methylong")
        if os.path.isdir(methylong_cache):
            normalized_aliases = [a.lower().replace("-", "").replace("_", "") for a in aliases]
            candidates = []
            for name in os.listdir(methylong_cache):
                if not name.endswith((".img", ".sif")):
                    continue
                norm_name = name.lower().replace("-", "").replace("_", "")
                if any(alias in norm_name for alias in normalized_aliases):
                    candidates.append(name)
            if candidates:
                candidates.sort(key=lambda f: (0 if f.endswith(".img") else 1, f))
                return os.path.join(methylong_cache, candidates[0])

        return None

    def _wrap_tool_chain_command(self, tool_name: str, raw_cmd: str, cwd: str = ""):
        """Wrap command in Singularity if an image exists, otherwise use TOOL_EXEC_ENV or current env."""
        image_path = self._resolve_image_path(tool_name)
        if not image_path:
            print(f'[Wrapper] No image found for {tool_name} — using configured exec env')
            return self._wrap_with_exec_env(raw_cmd, cwd=cwd)


        extra_lib = _find_dorado_lib_path_in_image(image_path) if tool_name == "dorado" else ""

        ld_parts = [p for p in [extra_lib, "/usr/local/nvidia/lib64", "/usr/local/nvidia/lib"] if p]
        ld_library_path = ":".join(ld_parts)

        bind_paths = set()
        
        for path in DATA_PATH.get(tool_name, {}).values():
            if not isinstance(path, str):
                continue
            abs_path = os.path.expanduser(path)
            if os.path.isdir(abs_path):
                bind_paths.add(abs_path)
        
        import re
        
        redirect_matches = re.findall(r'[>|]\s*(/[^\s>|]+)', raw_cmd)
        for path in redirect_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)
        
        output_matches = re.findall(r'(?:-o|--output)\s+(/[^\s-][^\s]*)', raw_cmd)
        for path in output_matches:
            parent_dir = os.path.dirname(path)
            if parent_dir and os.path.isdir(parent_dir):
                bind_paths.add(parent_dir)
        
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
        
        binds = ''
        for bind_path in sorted(bind_paths):
            binds += f"--bind {bind_path}:{bind_path} "

        # Write the inner command to a temp script so no shell quoting is needed
        # when embedding it into the singularity exec call.  This avoids the
        # incomplete escaping problem (backticks, $(), etc.) that arises when
        # splicing raw_cmd into a -c "..." string.
        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.sh', delete=False, prefix=f'{APP_SNAKE}_sing_',
            dir=_pick_script_dir(cwd),
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
