from abc import ABC, abstractmethod


class FunctionalAnalyzer(ABC):

    @abstractmethod
    def analyze(self, file_stats: dict) -> dict:
        """
        pass
        """
