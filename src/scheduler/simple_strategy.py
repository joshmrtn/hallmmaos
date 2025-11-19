from src.scheduler.base_strategy import BaseSchedulingStrategy
from src.services.task_data_service import TaskDataService
from src.models.task_types import Task, TaskStatus
from typing import List

class SimpleSchedulingStrategy(BaseSchedulingStrategy):
    """
    A simple scheduling strategy that selects tasks based on:
    1. Dependencies
    2. Priority
    3. Time since creation
    """

    def __init__(self, data_service: TaskDataService):
        """
        Creates a new SimpleSchedulingStrategy object.

        Currently it ignores RAM and CPU data.

        Args:
            data_service (TaskDataService): The data service layer for persistent 
            task storage. Needed for checking dependencies of tasks.
        """
        self._data_service = data_service

    def select_tasks(
            self,
            pending_tasks: List[Task],
            available_ram_mb: int,
            available_cpu_cores: float
    ) -> List[Task]:
        """
        Analyzes pending tasks and selects the best set to run now.

        Tasks are filtered by dependencies, sorted by priority (lowest first), 
        and time since creation (oldest first).
        It selects the top 10 tasks to run.
        """

        # Filter out blocked tasks
        unblocked_tasks: List[Task] = []
        for task in pending_tasks:
            is_task_blocked_by_dependency = False
            if task.blocked_by:
                # Task has dependencies listed. They must each be checked for completion.
                for blocking_task_id in task.blocked_by:
                    # Check if blocking_task_id references an actual task. If not, assume non-blocking.
                    if self._data_service.get_task_by_id(blocking_task_id) is None:
                        # Skip this task, it doesn't exist in the DB so we assume it's not blocking.
                        continue
                    # Check each dependency. If dependency is completed, it's non-blocking. Else, it's blocking.
                    blocking_task_status = self._data_service.get_task_by_id(blocking_task_id).status
                    blocking_statuses = {TaskStatus.FAILED, TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.NEW}
                    if blocking_task_status in blocking_statuses:
                        # Task is blocked by a dependency
                        is_task_blocked_by_dependency = True
                        break

            # If none of the dependencies are blocking, this task is unblocked.
            if is_task_blocked_by_dependency:
                    # skip this task
                    continue
            else:
                # Add this task to unblocked_tasks
                unblocked_tasks.append(task)

        # Return if no tasks available
        if not unblocked_tasks:
            return []
        
        # Sort unblocked_tasks by priority. If priorities are equal, sort by 
        # created_at (oldest first).
        sorted_tasks = sorted(
            unblocked_tasks,
            key=lambda task: (task.priority, task.created_at)
        )

        tasks_to_run = sorted_tasks[:10]
        return tasks_to_run