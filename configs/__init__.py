"""
configs 包入口。

加载顺序：
  1. 导入各子模块（触发其默认值初始化）
  2. 读取项目根目录的 config.yaml，将用户设置覆盖写入各子模块
  3. star-import 导出所有名称（此时已是覆盖后的值）

现有代码无需改动，继续 `from configs import XXX` 即可。
"""
import os as _os

# ── 1. 导入子模块对象（触发各自默认值初始化）─────────────────────────────────
from . import model_config  as _mc
from . import path_config   as _pc
from . import runtime_config as _rc
from . import auth_config   as _ac
from . import workflow_config as _wc
from . import i18n_config   as _ic


# ── 2. 读取并应用 config.yaml ─────────────────────────────────────────────────
def _apply_user_config():
    cfg_path = _os.path.join(_os.path.dirname(__file__), '..', 'config.yaml')
    if not _os.path.exists(cfg_path):
        return

    try:
        import yaml as _yaml
    except ImportError:
        print("[Config] Warning: PyYAML not installed — config.yaml ignored. "
              "Run: pip install pyyaml")
        return

    try:
        with open(cfg_path, encoding='utf-8') as _f:
            cfg = _yaml.safe_load(_f) or {}
    except Exception as e:
        print(f"[Config] Warning: failed to parse config.yaml: {e}")
        return

    # ── llm ──────────────────────────────────────────────────────────────────
    llm = cfg.get('llm') or {}
    if 'model_name' in llm:
        _mc.LLM_NAME = llm['model_name']
    if 'device' in llm:
        _rc.llm_args['device'] = llm['device']
    if isinstance(llm.get('model_paths'), dict):
        _mc.llm_model_path.update(llm['model_paths'])

    # ── tools.exec_env ────────────────────────────────────────────────────────
    tools = cfg.get('tools') or {}
    exec_env = tools.get('exec_env')
    if exec_env is not None:
        if isinstance(exec_env, dict) and exec_env.get('type'):
            _rc.TOOL_EXEC_ENV = exec_env
        else:
            _rc.TOOL_EXEC_ENV = None

    # ── data ─────────────────────────────────────────────────────────────────
    data = cfg.get('data') or {}
    if 'agent_data' in data:
        _agent_data = _os.path.abspath(_os.path.expanduser(str(data['agent_data'])))
        for _section in _pc.DATA_PATH.values():
            if isinstance(_section, dict) and 'base_data_dir' in _section:
                _section['base_data_dir'] = _agent_data
        _wf_sec = _pc.DATA_PATH.get('workflow', {})
        if _wf_sec:
            _wf_sec['work_dir']    = _os.path.join(_agent_data, 'nextflow_work')
            _wf_sec['nfcore_home'] = _os.path.join(_agent_data, '.nextflow')
    if 'dorado_models' in data:
        _pc.DATA_PATH['dorado']['dorado_models'] = _os.path.expanduser(
            str(data['dorado_models']))
    if 'dorado_sample_rate' in data:
        _pc.DATA_PATH['dorado']['sample_rate'] = int(data['dorado_sample_rate'])
    if 'singularity_image_dir' in data:
        _pc.IMAGE_PATH['image_store'] = _os.path.expanduser(
            str(data['singularity_image_dir']))
    if 'pipeline_dir' in data:
        _pc.DATA_PATH['workflow']['pipeline_dir'] = _os.path.expanduser(
            str(data['pipeline_dir']))
    if 'user_quota_gb' in data:
        _pc.USER_QUOTA_BYTES = int(float(data['user_quota_gb']) * 1024 ** 3)

    # ── users ─────────────────────────────────────────────────────────────────
    if isinstance(cfg.get('users'), dict):
        _ac.DEFAULT_USERS = {str(k): str(v) for k, v in cfg['users'].items()}

    # ── workflow ──────────────────────────────────────────────────────────────
    wf = cfg.get('workflow') or {}
    if 'profile' in wf:
        _wc.DEFAULT_WORKFLOW_ARGS['profile'] = wf['profile']
    if 'extra_args' in wf:
        _wc.DEFAULT_WORKFLOW_ARGS['extra_args'] = wf['extra_args']
    if 'max_memory' in wf:
        _wc.MAX_WORKFLOW_RESOURCES['max_memory'] = wf['max_memory']
    if 'max_time' in wf:
        _wc.MAX_WORKFLOW_RESOURCES['max_time'] = wf['max_time']
    if 'max_cpus' in wf:
        _wc.MAX_WORKFLOW_RESOURCES['max_cpus'] = wf['max_cpus']

    # ── language ──────────────────────────────────────────────────────────────
    if 'language' in cfg:
        _ic.DEFAULT_LANG = str(cfg['language'])

    print(f"[Config] Loaded config.yaml  (model={_mc.LLM_NAME}  device={_rc.llm_args.get('device')}  lang={_ic.DEFAULT_LANG})")


_apply_user_config()


# ── 3. star-import（覆盖后的值）────────────────────────────────────────────────
from .model_config import *    # noqa: E402, F401, F403
from .tool_config import *     # noqa: E402, F401, F403
from .path_config import *     # noqa: E402, F401, F403
from .rag_config import *      # noqa: E402, F401, F403
from .runtime_config import *  # noqa: E402, F401, F403
from .i18n_config import *     # noqa: E402, F401, F403
