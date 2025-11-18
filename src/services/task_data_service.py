from src.models.task_types import Task, TaskStatus
from src.data.base_task_repository import BaseTaskRepository
from src.data.json_task_repository import JsonTaskRepository
from src.config.config_manager import ConfigManager

from typing import Optional, Dict, Tuple, List, Any
from pathlib import Path

class TaskDataService:
    """
    Orchestration layer used to manage active tasks and archived tasks.

    This service encapsulates the logic for deciding which repository to use, 
    handling task movement from active to archive and enforcing business rules.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the service by loading configurations.

        Args:
            config_manager (ConfigManager): The application's configuration manager.
        """
        # Get data path from configuration.

        self._config = config_manager

        repo_config = self._config.get("tasks_data", {})

        base_data_dir = repo_config.get("data_base_dir")
        if not base_data_dir:
            raise ValueError("Configuration key 'tasks_data.data_base_dir' is missing.")
        base_path = Path(base_data_dir)

        # Initialize repositories.
        active_file = repo_config.get("active_repo_file")
        archive_file = repo_config.get("archive_repo_file")

        # Active repository (for PENDING, RUNNING, NEW tasks).
        self._active_repo: BaseTaskRepository = JsonTaskRepository(
            file_path=base_path / active_file
        )

        # Archive repository (for COMPLETED, FAILED, CANCELLED tasks).
        self._archive_repo: BaseTaskRepository = JsonTaskRepository(
            file_path=base_path / archive_file
        )

        print(f"TaskDataService initialized with Active Repo: {base_path / active_file}")        
        print(f"TaskDataService initialized with Archive Repo: {base_path / archive_file}")


    def add_task(self, task: Task) -> None:
        """
        Adds a new task. New tasks always go to the active repository.

        Args:
            task (Task): The Task object to add to the repository.
        """
        if task.status != TaskStatus.NEW:
            raise ValueError("New tasks must start with TaskStatus.NEW.")
        
        # TODO: Add admission control here. Check PENDING count and reject if too many.

        self._active_repo.add(task)


    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """
        Retrieves a task from the active repo first, then the archive repo.

        Args:
            task_id (str): The unique ID of the task to retrieve.
        """
        task = self._active_repo.get_by_id(task_id)
        if task:
            return task
        # Fallback to archive
        return self._archive_repo.get_by_id(task_id)
    

    def update_task(self, updated_task: Task) -> None:
        """
        Updates an existing task with a new Task instance.
        Handles the transition from Active to Archive (or vice versa) if the new 
        task status indicates a change from active to archive.

        Args:
            updated_task (Task): The new task instance. It will replace the 
                                 existing Task of the same task_id.
        """
        finished_statuses = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        active_statuses = {TaskStatus.NEW, TaskStatus.PENDING, TaskStatus.RUNNING}

        # --- Handle movement from Active < --- > Archive repos
        new_status = updated_task.status

        if new_status in finished_statuses:
            # --- Active -> Archive Movement
            try:
                self._archive_repo.update(updated_task)
            except KeyError:
                self._archive_repo.add(updated_task)

            try:
                self._active_repo.delete_by_id(updated_task.task_id)
            except KeyError:
                # Not found in active repo, no need to do anything.
                pass

        elif new_status in active_statuses:
            # --- Archive -> Active Movement
            try:
                self._active_repo.update(updated_task)
            except KeyError:
                self._active_repo.add(updated_task)

            try:
                self._archive_repo.delete_by_id(updated_task.task_id)
            except KeyError:
                # Not found in archive repo, no need to do anything.
                pass

        else:
            # --- In-Place Update
            # This just ensures that the status is updated regardless of the current
            # enum.
            try:
                self._active_repo.update(updated_task)
            except KeyError:
                try:
                    self._archive_repo.update(updated_task)
                except KeyError:
                    # If it's not in either, raise an error.
                    raise KeyError(f"Task ID {updated_task.task_id} not found in Active or Archive repositories for update.")
                

    def get_pending_count(self) -> int:
        """
        Retrieves the current count of PENDING tasks from the active repository.
        """
        return self._active_repo.get_pending_count()
    

    def query_active_tasks(
            self,
            filter_status: Optional[TaskStatus] = None,
            limit: int = 100,
            **kwargs: Any
    ) -> Tuple[List[Task], Optional[Dict[str, Any]]]:
        """
        Queries the active repository for tasks (e.g., for finding the next batch to run).

        Args:
            filter_status (TaskStatus): The status to filter by (PENDING, RUNNING, NEW).
            limit (int): The maximum number of Tasks to retrieve.
            **kwargs: Optional keyword arguments to pass to JsonTaskRepository.query().
        """
        return self._active_repo.query(
            filter_status=filter_status,
            limit=limit,
            **kwargs
        )
    

    def query_all_tasks(
        self,
        filter_status: Optional[TaskStatus] = None,
        limit: int = 100,
        **kwargs: Any
    ) -> Tuple[List[Task], Optional[Dict[str, Any]]]:
        """
        Queries all tasks from both repos for reporting or monitoring.

        Prioritizes fetching from the Active repo first, then the Archive repo 
        to fill the limit.

        Args:
            filter_status (TaskStatus): The status to filter by (Optional).
            limit (int): The maximum number of results to return.
            **kwargs: Optional keyword arguments that will be passed to JsonTaskRepository.query()
        """
        results: List[Task] = []
        next_archive_key: Optional[Dict[str, Any]] = None

        active_statuses = {TaskStatus.NEW, TaskStatus.PENDING, TaskStatus.RUNNING}
        finished_statuses = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

        # Query Active Repository
        # Only query Active if filter is for an active status or is None.
        if (kwargs.get('exclusive_start_key') is None) and (filter_status is None or filter_status in active_statuses):
            # Filter out kwargs for the active query
            active_kwargs = {k: v for k, v in kwargs.items() if k != 'exclusive_start_key'}
            active_results, _ = self._active_repo.query(
                filter_status=filter_status,
                limit=limit,
                **active_kwargs
            )

            results.extend(active_results)

        if len(results) < limit and (filter_status is None or filter_status in finished_statuses):
            remaining_limit = limit - len(results)

            archive_results, next_archive_key = self._archive_repo.query(
                filter_status=filter_status,
                limit=remaining_limit,
                **kwargs
            )

            results.extend(archive_results)

        # If the results reached the limit and came from the archive repo,
        # the next_archive_key is the new cursor. Otherwise, the query is finished.

        final_next_key = None
        if next_archive_key is not None:
            # We return archive's cursor directly if it indicates more tasks
            final_next_key = next_archive_key

        return results, final_next_key
