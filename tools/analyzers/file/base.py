from abc import ABC, abstractmethod


class FileAnalyzer(ABC):

    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """
        pass
        """
