import importlib
import logging
import sys
import threading

from configs.model_config import LLM_NAME, llm_model_path
from configs.runtime_config import llm_args

logging.getLogger("transformers").setLevel(logging.ERROR)


def import_llm_initializer(module_name: str, function_name: str = "get_llm"):
    full_module_path = f"LLM.{module_name}"
    try:
        spec = importlib.util.find_spec(full_module_path)
        if spec is None:
            raise ModuleNotFoundError(f"Unable to find the module: {full_module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_path] = module
        spec.loader.exec_module(module)
        if not hasattr(module, function_name):
            raise AttributeError(f"The function '{function_name}' was not found in '{module_name}'.")
        return getattr(module, function_name)
    except (ModuleNotFoundError, AttributeError) as e:
        print(f"Fatal error: Dynamic import of LLM failed: {e}")
        raise e


_MODEL_CACHE: dict = {}
_model_init_lock = threading.Lock()
# 序列化所有 GPU 推理：本地单卡模型不支持真正并发推理
_inference_lock = threading.Lock()


class _ThreadSafeLLMWrapper:
    """
    将调用参数（temperature / enable_thinking）保存在 wrapper 实例上，
    invoke() 时原子地设置到底层模型并持锁推理，确保：
      1. 参数不会被其他线程覆盖
      2. GPU 不会被多线程同时占用
    """
    def __init__(self, model, temperature: float, enable_thinking: bool):
        self._model = model
        self.temperature = temperature
        self.enable_thinking = enable_thinking

    def invoke(self, prompt: str):
        with _inference_lock:
            self._model.temperature = self.temperature
            self._model.enable_thinking = self.enable_thinking
            return self._model.invoke(prompt)

    # 透传 stream / batch（当前未用，保留接口兼容）
    def stream(self, prompt: str):
        with _inference_lock:
            self._model.temperature = self.temperature
            self._model.enable_thinking = self.enable_thinking
            yield from self._model.stream(prompt)


def get_llm_instance(is_planner: bool = False, temperature: float = 0.01):
    """
    返回一个线程安全的 LLM wrapper。
    每次调用返回新 wrapper 对象（携带独立的参数副本），底层模型全局共享。
    所有 invoke() 调用通过 _inference_lock 串行化，防止 GPU 并发冲突。
    """
    with _model_init_lock:
        if "llm" not in _MODEL_CACHE:
            print("[System] Initializing the model for the first time, please wait ..")
            llm_func = import_llm_initializer(module_name=LLM_NAME)
            llm_path = llm_model_path[LLM_NAME]
            _MODEL_CACHE["llm"] = llm_func(llm_path, device=llm_args['device'])

    model = _MODEL_CACHE["llm"]
    if is_planner:
        return _ThreadSafeLLMWrapper(model, temperature=temperature, enable_thinking=False)
    else:
        return _ThreadSafeLLMWrapper(model, temperature=0.7, enable_thinking=True)