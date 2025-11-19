from abc import ABC, abstractmethod
from typing import Optional, List
from src.models.task_types import Task


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
    def update_task(self, task: Task):
        """
        Update an existing Task in the queue by passing a new Task object with 
        updated fields. If a Task is provided with a task_id that doesn't exist, 
        this will throw an error.
        
        Args:
            task (Task): The new Task object which will replace the existing task 
                        with the matching task_id.
        """
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
