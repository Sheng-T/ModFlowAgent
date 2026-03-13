import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.language_models import BaseLLM
from typing import Dict, Any


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

    model = AutoModelForCausalLM.from_pretrained(
        model_dir,
        torch_dtype=dtype,
        device_map=device,
        # 避免在 pipeline 中重复进行 thinking content 解析，
        # LangChain Agent 会通过 PromptTemplate 处理输入
    )

    # 2. 创建 Hugging Face Pipeline
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        temperature=temperature if not do_sample else 0.01,
        do_sample=do_sample,
        # 设置停止标记（如果模型有特定的停止 ID，可在这里设置）
        eos_token_id=tokenizer.eos_token_id,
        # 确保 LangChain 能够正确处理模型输出
        # 你的 LLM 可能需要将 pad_token_id 设置为 eos_token_id 以避免警告
        pad_token_id=tokenizer.eos_token_id
    )

    # 3. 将 Pipeline 封装成 LangChain LLM
    llm = HuggingFacePipeline(pipeline=pipe)

    print("--- 模型加载完成，已封装为 LangChain LLM ---")
    return llm

# 示例调用
# 假设你的模型在本地路径 /path/to/your/qwen1.5-0.5b-chat
# llm = get_llm(model_dir="/path/to/your/qwen1.5-0.5b-chat")
# response = llm.invoke("什么是 Agent？")
# print(response)