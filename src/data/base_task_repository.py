from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from src.models.task_types import Task, TaskStatus

class BaseTaskRepository(ABC):
    """
    Abstract interface for handling all CRUD operations for Task objects.
    """

    @abstractmethod
    def add(self, task: Task) -> None:
        """Stores a new Task."""
        pass

    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Retrieves a Task by its ID.
        
        Args:
            task_id (str): The unique Task ID of the Task to retrieve.

        Returns:
            The Task object matching that ID, or None if not found.
        """
        pass

    @abstractmethod
    def update(self, task: Task) -> None:
        """
        Updates an existing Task in storage.
        
        Args:
            task (Task): The new Task object. It will replace the Task with the 
            same ID in storage.
        """
        pass

    @abstractmethod
    def delete_by_id(self, task_id: str) -> None:
        """
        Removes a Task from storage.

        Args:
            task_id (str): The unique ID of the task to remove.
        """
        pass

    @abstractmethod
    def query(
        self, 
        filter_status: Optional[TaskStatus] = None,
        filter_agent_id: Optional[str] = None,
        filter_correlation_id: Optional[str] = None,
        sort_field: str = 'created_at',
        sort_ascending: bool = True,
        limit: int = 10,
        exclusive_start_key: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Task], Optional[Dict[str, Any]]]:
        """
        Retrieves a page of Tasks, optionally filtered and sorted.

        A flexible query method 
        
        Args:
            filter_status (TaskStatus): The status to filter by (Optional).
            filter_agent_id (str): The agent ID to filter by (Optional).
            filter_correlation_id (str): The correlation ID to filter by (Optional).
            sort_field (str): default = 'created_at' - the field to sort by.
            sort_ascending (boolean): Whether to sort ascending (True) or descending (False).
            limit (int): The maximum number of Tasks returned.
            exclusive_start_key (Dict): Used for paginated querying, start at the given key.

        Returns:
            A tuple containing the list of Tasks, and the next curson/token for pagination. 
            If this dict is not None, it signals that there are more Tasks that may be queried, 
            and this dict can be passed into the exclusive_start_key parameter to query the 
            next page.
        """
        pass

    @abstractmethod
    def get_pending_count(self) -> int:
        """
        Retrieves the count of tasks in PENDING status.
        """
        pass