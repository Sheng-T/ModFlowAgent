# LLM/gemini_model.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, List


def get_llm(
        model_name: str = "gemini-1.5-flash",  # 或者 "gemini-1.5-pro"
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
):
    """
 初始化 Gemini 模型。
 注意：Gemini 是 ChatModel，原生支持工具调用和长上下文。
 """
    # 也可以在环境变量中设置 GOOGLE_API_KEY
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("请提供 GOOGLE_API_KEY 或设置环境变量")

    print(f"--- 正在初始化 Gemini 模型: {model_name} ---")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_tokens,
        **kwargs
    )

    return llm