import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from src.models.task_types import Task, TaskStatus
from src.data.base_task_repository import BaseTaskRepository

class JsonTaskRepository(BaseTaskRepository):
    """
    Concrete implementation of BaseTaskRepository using a local JSON file 
    for persistence. Intended for development/testing and simple environments.
    """

    def __init__(self, file_path: Path):
        """
        Creates a JsonTaskRepository.

        Args:
            file_path (Path): The file Path object to use for json task persistence.
        """
        self._file_path = file_path
        # Use in-memory cache for fast reads.
        self._tasks: Dict[str, Task] = self._load_from_files()

    def _load_from_files(self) -> Dict[str, Task]:
        """
        Loads tasks from the persistent JSON file. Used by constructor.

        Returns:
            The Tasks dict.
        """
        if not self._file_path.exists():
            return {}
        
        try:
            with open(self._file_path, 'r') as f:
                raw_data = json.load(f)

            tasks = {}
            # Create Pydantic Task objects from raw dictionary data.
            for task_id, data in raw_data.items():
                try:
                    tasks[task_id] = Task(**data)
                except Exception as e:
                    print(f"Error converting Task {task_id} to Pydantic format: {e}")
            return tasks
        
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load tasks from {self._file_path}. Starting clean. Error: {e}")
            return {}
        
    
    def _save_to_file(self) -> None:
        """Saves current Tasks from memory to persistent JSON file."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        # Dump Tasks to serializable dictionary.
        serializable_data = {
            task_id: task.model_dump(mode='json')
            for task_id, task in self._tasks.items()
        }

        try:
            with open(self._file_path, 'w') as f:
                json.dump(serializable_data, f, indent=4, default=str)
        except IOError as e:
            print(f"Error saving tasks to {self._file_path}: {e}")

    def add(self, task: Task) -> None:
        """
        Implements contract: add Task to storage.
        
        Args:
            task (Task): The Task to add.
        """
        if task.task_id in self._tasks:
            raise ValueError(f"Task ID {task.task_id} already exists.")
        
        self._tasks[task.task_id] = task
        self._save_to_file()

    def get_by_id(self, task_id: str) -> Optional[Task]:
        """
        Implements contract: Get task by ID.
        
        Args:
            task_id (str): The ID of the task to retrieve.
        Returns:
            The Task matching task_id, or None if it doesn't exist.
        """
        return self._tasks.get(task_id)
    
    def update(self, task: Task) -> None:
        """
        Implements contract: Update task.
        
        Args:
            task (Task): The new Task object. Replaces existing Task object with 
            matching task_id.  
        """
        if task.task_id not in self._tasks:
            raise KeyError(f"Task ID {task.task_id} not found for update.")
        
        self._tasks[task.task_id] = task
        self._save_to_file()

    def delete_by_id(self, task_id: str) -> None:
        """
        Implements contract: Delete Task by ID.
        
        Args:
            task_id (str): The unique ID of the task to delete.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_to_file()

    def get_pending_count(self) -> int:
        """
        Implements contract: Get count of pending Tasks.

        Returns:
            The count of Tasks with PENDING status.
        """
        count = sum(1 for task in self._tasks.values() if task.status == TaskStatus.PENDING)
        return count
    

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
        Implements contract: Retrieves a page of Tasks, optionally filtered and sorted.

        A flexible query method. Filters and sorts from in-memory task cache.
        
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
        # Start with the whole in-memory list of Tasks
        results = list(self._tasks.values())

        # Filtering:
        if filter_status:
            results = [t for t in results if t.status == filter_status]
        if filter_agent_id:
            results = [t for t in results if t.agent_id == filter_agent_id]
        if filter_correlation_id:
            results = [t for t in results if filter_correlation_id in t.correlation_ids]

        # Sorting
        try:
            results.sort(key=lambda t: getattr(t, sort_field), reverse=not sort_ascending)
        except AttributeError:
            # Fallback to sorting by date created.
            results.sort(key=lambda t: t.created_at, reverse=not sort_ascending)

        # Pagination
        start_index = 0
        if exclusive_start_key and 'last_id' in exclusive_start_key:
            try:
                # Try to find last_id in results.
                last_id = exclusive_start_key['last_id']
                start_index = next(i for i, t in enumerate(results) if t.task_id == last_id) + 1
            except StopIteration:
                start_index = 0 # Go back to start if not found.

        end_index = start_index + limit
        page = results[start_index:end_index]

        next_key = None
        if end_index < len(results):
            next_key = {'last_id': page[-1].task_id}

        return page, next_key