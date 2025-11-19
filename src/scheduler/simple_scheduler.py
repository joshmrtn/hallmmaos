
from src.scheduler.base_scheduler import BaseScheduler
from src.scheduler.base_strategy import BaseSchedulingStrategy
from src.models.task_types import Task, TaskStatus
from src.resources.base_monitor import BaseResourceMonitor
from src.services.task_data_service import TaskDataService

from typing import Optional, List

class SimpleScheduler(BaseScheduler):
    """
    A concrete implementation of the BaseScheduler.
    Relies on injected components for task persistence, resource monitoring 
    and scheduling strategy.
    """

    def __init__(self, monitor: BaseResourceMonitor, strategy: BaseSchedulingStrategy, data_service: TaskDataService):
        """
        Creates a new SimpleScheduler object.

        Args:
            monitor (BaseResourceMonitor): The resource monitor used for gathering resource information.
            strategy (BaseSchedulingStrategy): The strategy used for task execution ordering.
            data_service (TaskDataService): The Task persistence service layer.
        """
        self._monitor = monitor
        self._strategy = strategy
        self._data_service = data_service
        self._next_tasks_to_run: List[Task] = []



    def submit_task(self, task: Task):
        """
        Add a new message/job to the scheduler's queue for processing.

        Uses the TaskDataService layer to validate and add the task to 
        persistent storage.

        Args:
            task: The fully instantiated Task object derived from a chat
                  event or an internal command.
        """
        self._data_service.add_task(task)


    def get_next_task(self) -> Optional[Task]:
        """
        Returns the task that should be executed next.

        Uses the locally cached queue that is checked first, refreshing the 
        queue using the SchedulingStrategy if empty.
        
        Returns:
            The next Task object to be executed, or None if the queue is empty 
            or if no tasks are ready to run.
        """
        # Check local queue first.
        if self._next_tasks_to_run:
            return self._next_tasks_to_run.pop(0)
        
        # Refresh queue using strategy
        # Get system load information
        available_ram_mb = self._monitor.get_available_ram_mb()
        available_cpu_cores = self._monitor.get_available_cpu_cores()

        # Get available tasks (NEW/PENDING).
        new_tasks, _ = self._data_service.query_active_tasks(
            filter_status=TaskStatus.NEW,
            limit=100
        )
        pending_tasks, _ = self._data_service.query_active_tasks(
            filter_status=TaskStatus.PENDING,
            limit=100
        )
        tasks_available_to_schedule = new_tasks + pending_tasks

        selected_tasks = self._strategy.select_tasks(
            pending_tasks=tasks_available_to_schedule,
            available_ram_mb=available_ram_mb,
            available_cpu_cores=available_cpu_cores
        )

        if selected_tasks:
            for task in selected_tasks:
                # Set task to RUNNING status
                updated_task = task.model_copy(update={"status": TaskStatus.RUNNING})
                self._data_service.update_task(updated_task)
            # Update locally cached queue and return first task
            self._next_tasks_to_run.extend(selected_tasks)
            return self._next_tasks_to_run.pop(0)
        # No available tasks to run!
        return None
        


    def update_task(self, task: Task):
        """
        Update an existing Task's information, e.g., to mark a task as completed, 
        update checkpoint data, execution metrics, or other data fields.

        Args:
            task (Task): The updated task, which will replace the existing Task 
                        whose task_id matches.
        """
        self._data_service.update_task(task)


    def get_pending_tasks(self) -> List[Task]:
        """
        Retrieves all tasks currently waiting in the queue.

        This is primarily used for monitoring or re-prioritization.

        Returns:
            The list of all pending tasks in the queue.
        """
        tasks, _ = self._data_service.query_active_tasks(filter_status=TaskStatus.PENDING, limit = 1000)
        return tasks