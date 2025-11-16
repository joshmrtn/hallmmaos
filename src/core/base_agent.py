from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.scheduler.task import Task

class BaseAgent(ABC):
    """
    Abstract interface for all executable agents.
    """

    @property
    @abstractmethod
    def agent_id(self) -> str:
        """The unique, immutable identifier for this agent instance."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """The human-readable name/persona of the agent."""
        pass

    @abstractmethod
    def handle_task(self, task: Task) -> Task:
        """
        Receives a Task object and executes the necessary LLM calls, tool usage, 
        and state updates to progress the task.

        Args:
            task (Task): The Task object to be processed, typically in the RUNNING status.
        
        Returns:
            The updated Task object, reflecting the new status (e.g. COMPLETE, PAUSED, 
            or still RUNNING) and any updated checkpoint data.
        """
        pass





    @abstractmethod
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Retrieves tools available to the agent.

        Returns:
            A list of standardized tool dictionaries.
        """
        pass