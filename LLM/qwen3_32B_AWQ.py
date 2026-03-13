import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.language_models import BaseLLM
from typing import Dict, Any
import os
os.environ["AWQ_USE_TRITON"] = "0"

def get_llm(
        model_dir: str,
        device: str = "auto",
        torch_dtype: Any = "auto",
        max_new_tokens: int = 1024,  # 减少到更常用的值
        temperature: float = 0.01,
        do_sample: bool = False,
) -> BaseLLM:
    """
    加载 Hugging Face 模型并封装成 LangChain LLM 对象。
    """
    print(f"--- 正在加载模型: {model_dir} ---")

    # 1. 加载分词器和模型
    tokenizer = AutoTokenizer.from_pretrained(model_dir)

    # 确定 torch_dtype
    if torch_dtype == "auto":
        # 尝试使用 bfloat16 优化显存，否则使用 float16
        dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.get_device_properties(
            0).major >= 8 else torch.float16
    elif isinstance(torch_dtype, str) and torch_dtype.lower() == 'fp16':
        dtype = torch.float16
    else:
        dtype = torch_dtype

    print(f'dtype: {dtype}')

    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=dtype,
        device_map=device,
        # 避免在 pipeline 中重复进行 thinking content 解析，
        # LangChain Agent 会通过 PromptTemplate 处理输入
    )

    try:
        from awq.modules.linear import WQLinear_GEMM
        print("--- 正在强制切换 AWQ 后端至 GEMM 以规避 Triton 编译错误 ---")

        for name, module in model.named_modules():
            if hasattr(module, 'autotune_gen'):
                # 禁用 Triton 自动调优，这通常会迫使它回退或停止即时编译
                module.autotune_gen = False
    except ImportError:
        print("无法导入 WQLinear_GEMM，请确保已安装 autoawq")

    # 2. 创建 Hugging Face Pipeline
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        top_k=50 if do_sample else None,  # top_k=50 是常见默认
        top_p=0.95 if do_sample else None,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id,
        return_full_text=False,
    )

    # 3. 将 Pipeline 封装成 LangChain LLM
    llm = HuggingFacePipeline(pipeline=pipe)

    print("--- 模型加载完成，已封装为 LangChain LLM ---")
    return llm

# 示例调用
# 假设你的模型在本地路径 /path/to/your/qwen1.5-0.5b-chat
llm = get_llm(model_dir="/ni_data/users/shengtao/model/qwen3-32b-awq/models--Qwen--Qwen3-32B-AWQ/snapshots/0499c3ac83fdef8810b907a23894ba91e95eddd8/")
response = llm.invoke("什么是 Agent？")
print(response)