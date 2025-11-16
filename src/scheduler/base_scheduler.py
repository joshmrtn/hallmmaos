from abc import ABC, abstractmethod
from typing import Optional, List
from .task import Task


class BaseScheduler(ABC):
    """
    Abstract interface for managing a queue of tasks.
    The scheduler manages a queue of submitted tasks, determines execution
    order based on metrics (priority, estimated duration), and tracks
    historical performance to refine future planning.
    """

    @abstractmethod
    def submit_task(self, task: Task):
        """
        Add a new message/job to the scheduler's queue for processing.

        Args:
            task: The fully instantiated Task object derived from a chat
                  event or an internal command.
        """
        pass

    @abstractmethod
    def get_next_task(self) -> Optional[Task]:
        """
        Returns the task that should be executed next.
        
        Returns:
            The next Task object to be executed, or None if the queue is empty 
            or if no tasks are ready to run.
        """
        pass

    @abstractmethod
    def update_status(self, task_id: str, metrics: dict):
        """
        Record the outcome and performance metrics of a completed or checkpointed task.
        
        This data is used to refine historical performance models, and is critical 
        to updating checkpoint information (state) when a task is paused.
        
        Args:
            task_id: Unique identifier for the task.
            metrics: A dictionary containing execution metrics."""
        pass

    @abstractmethod
    def get_pending_tasks(self) -> List[Task]:
        """
        Retrieves all tasks currently waiting in the queue.

        This is primarily used for monitoring or re-prioritization.

        Returns:
            The list of all tasks in the queue.
        """
        pass
