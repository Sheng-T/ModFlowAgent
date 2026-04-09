from abc import ABC, abstractmethod


class FunctionalAnalyzer(ABC):
    """功能判断基类：基于文件统计结果做规则判断，不调用 LLM。"""

    @abstractmethod
    def analyze(self, file_stats: dict) -> dict:
        """
        输入 FileAnalyzer 返回的统计 dict，
        输出结构化判断 dict（含 grade/pattern/assessment 等字段）。
        出错时返回 {"error": str}。
        """
