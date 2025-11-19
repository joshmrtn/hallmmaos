from abc import ABC, abstractmethod
from typing import List
from src.models.task_types import Task

class BaseSchedulingStrategy(ABC):
    """
    Abstract interface for choosing task execution order.
    """
    @abstractmethod
    def select_tasks(
        self,
        pending_tasks: List[Task],
        available_ram_mb: int,
        available_cpu_cores: float
    ) -> List[Task]:
        """
        Analyzes a pool of tasks and selects the best set of tasks to run now.
        
        The strategy is constrained by task dependencies (blocked_by) and resource 
        limits (RAM, CPU).

        Args:
            pending_tasks (Task[]): A list of all Task objects currently in PENDING status.
            available_ram_mb (int): Total usable RAM capacity available on the host/node, 
                                    sourced from BaseResourceMonitor.
            available_cpu_cores (float): The total usable CPU core capacity available.

        Returns:
            A list of Task objects selected for immediate execution, ordered by priority 
            or execution sequence. Returns an empty list if no tasks can be executed 
            right now.
        """
        pass


