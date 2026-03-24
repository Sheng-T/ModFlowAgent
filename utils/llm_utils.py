import importlib
import logging
import sys

from configs.model_config import LLM_NAME, llm_model_path
from configs.runtime_config import llm_args

logging.getLogger("transformers").setLevel(logging.ERROR)

# 简化占位符 LLM

def import_llm_initializer(module_name: str, function_name: str = "get_llm"):
    """
    动态导入指定模块中的 LLM 初始化函数。

    Args:
        module_name: 模块名称 (例如 "qwen_model")。
        function_name: 要导入的函数名称 (例如 "get_llm")。

    Returns:
        导入的函数对象 (Callable)。
    """
    # 构造完整的模块路径，例如: agent.LLM.qwen_model
    full_module_path = f"LLM.{module_name}"

    try:
        # 尝试使用 importlib 导入模块
        spec = importlib.util.find_spec(full_module_path)
        if spec is None:
            raise ModuleNotFoundError(f"无法找到模块: {full_module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_path] = module
        spec.loader.exec_module(module)

        # 从模块中获取指定的函数
        if not hasattr(module, function_name):
            raise AttributeError(f"模块 '{module_name}' 中没有找到函数 '{function_name}'。")

        return getattr(module, function_name)

    except (ModuleNotFoundError, AttributeError) as e:
        print(f"致命错误：动态导入 LLM 失败: {e}")
        raise e


_MODEL_CACHE = {}
def get_llm_instance(is_planner: bool = False, temperature=0.01):
    """
    根据用途获取 LLM 实例。
    is_planner: True 则获取低随机性、关闭思考的 Planner 专用模型。
    """
    global _MODEL_CACHE

    if "llm" not in _MODEL_CACHE:
        print("[System] 首次初始化模型，请稍候...")
        llm_func = import_llm_initializer(module_name=LLM_NAME)
        llm_path = llm_model_path[LLM_NAME]
        # 这里只加载一次
        _MODEL_CACHE["llm"] = llm_func(llm_path, device=llm_args['device'])

    model = _MODEL_CACHE["llm"]
    if is_planner:
        model.temperature = 0.01
        model.enable_thinking = False
    else:
        model.temperature = 0.7
        model.enable_thinking = True
    return model