from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseOrchestrator(ABC):
    """
    Abstract interface for the central command and control unit of the agent system.

    The orchestrator is responsible for initialization, event handling, creating 
    Tasks, and managing the overall Task lifecycle via the Scheduler.
    """

    @abstractmethod
    def initialize_system(self) -> None:
        """
        Initializes all system components: loads agents, connects adapters, and 
        sets up the memory and scheduler.
        """
        pass

    @abstractmethod
    def start_polling_loop(self) -> None:
        """
        Initializes the main operational cycle, involving:
        1. Polling chat adapters for new messages/events.
        2. Creating new Tasks based on those events.
        3. Triggering the Scheduler to run pending tasks.
        """
        pass

    @abstractmethod
    def process_incoming_event(self, event_data: Dict[str: Any]) -> None:
        """
        Handles a single external event (such as a message from a chat adapter).

        This involves identifying the recipient agent, creating a Task object, and 
        handing it off to the Scheduler.

        Args:
            event_data (Dict): The standardized dictionary representing the external event.
        """
        pass

    @abstractmethod
    def check_and_run_tasks(self) -> List[str]:
        """
        Instructs the Scheduler to select runnable tasks and executes them using 
        the appropriate Agent.

        Returns:
            A list of IDs for the tasks that were processed or completed in this cycle.
        """
        pass