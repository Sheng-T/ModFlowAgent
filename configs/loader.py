
from typing import Dict

from . import model_config, path_config, rag_config, runtime_config, tool_config, workflow_config


def load_all_configs() -> Dict[str, object]:
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
