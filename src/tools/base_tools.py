from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Abstract class defining the common interface for all agent tools."""
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Runs the tool logic and returns a string result for the LLM."""
        pass
    