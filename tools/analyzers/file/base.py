from abc import ABC, abstractmethod


class FileAnalyzer(ABC):
    """文件统计分析基类：只做数字统计，不调用 LLM，不做判断。"""

    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """
        分析文件，返回结构化统计 dict。
        所有数值均为 Python 原生类型（int / float），方便 JSON 序列化。
        出错时返回 {"error": str} 而不是抛出异常。
        """
