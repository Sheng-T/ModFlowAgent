"""
配置加载器：集中导出配置模块，提供简单校验/访问接口。
该文件为非侵入式的兼容层，现有代码可继续通过 `from configs import ...` 使用。
"""
from typing import Dict

from . import model_config, path_config, rag_config, runtime_config, tool_config, workflow_config


def load_all_configs() -> Dict[str, object]:
    """返回一个字典，包含所有子配置模块的引用。"""
    return {
        "model_config": model_config,
        "path_config": path_config,
        "rag_config": rag_config,
        "runtime_config": runtime_config,
        "tool_config": tool_config,
        "workflow_config": workflow_config,
    }


DEFAULTS = load_all_configs()


__all__ = ["load_all_configs", "DEFAULTS"]
