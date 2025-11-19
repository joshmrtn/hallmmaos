import pytest
from unittest.mock import MagicMock, create_autospec
from datetime import datetime
from src.scheduler.simple_scheduler import SimpleScheduler
from src.services.task_data_service import TaskDataService
from src.resources.base_monitor import BaseResourceMonitor
from src.scheduler.base_strategy import BaseSchedulingStrategy
from src.models.task_types import Task, TaskStatus

@pytest.fixture
def mock_data_service():
    return create_autospec(TaskDataService, instance=True)

@pytest.fixture
def mock_monitor():
    return create_autospec(BaseResourceMonitor, instance=True)

@pytest.fixture
def mock_strategy():
    return create_autospec(BaseSchedulingStrategy, instance=True)

@pytest.fixture
def scheduler(mock_monitor, mock_strategy, mock_data_service):
    return SimpleScheduler(
        monitor=mock_monitor,
        strategy=mock_strategy,
        data_service=mock_data_service
    )

@pytest.fixture
def sample_task():
    return Task(
        task_id="task-1",
        agent_id="agent-1",
        source_domain="test",
        source_topic="test",
        input_message="data",
        priority=1,
        status=TaskStatus.PENDING
    )

# --- Tests ---

def test_submit_task_delegates_to_service(scheduler, mock_data_service, sample_task):
    """Tests that submit_task simply calls the data service."""
    scheduler.submit_task(sample_task)
    mock_data_service.add_task.assert_called_once_with(sample_task)

def test_update_task_delegates_to_service(scheduler, mock_data_service, sample_task):
    """Tests that update_task simply calls the data service"""
    scheduler.update_task(sample_task)
    mock_data_service.update_task.assert_called_once_with(sample_task)

def test_get_pending_tasks_delegates_to_service(scheduler, mock_data_service):
    """Tests getting pending tasks queries the service with correctl filters."""
    mock_data_service.query_active_tasks.return_value = ([], None)

    scheduler.get_pending_tasks()

    mock_data_service.query_active_tasks.assert_called_once_with(
        filter_status=TaskStatus.PENDING,
        limit=1000
    )

def test_get_next_task_uses_local_queue_if_populated(scheduler, mock_data_service, sample_task):
    """Tests that if the local queue has tasks, it doesn't query the service."""
    scheduler._next_tasks_to_run = [sample_task]

    next_task = scheduler.get_next_task()

    assert next_task == sample_task
    assert len(scheduler._next_tasks_to_run) == 0
    # Ensure service was NOT queried
    mock_data_service.query_active_tasks.assert_not_called()

def test_get_next_task_refreshes_queue_if_empty(
        scheduler, mock_monitor, mock_strategy, mock_data_service, sample_task
):
    """
    Tests the full flow when local queue is empty:
    1. Checks resources
    2. Queries service for PENDING/NEW tasks
    3. Calls strategy to select tasks
    4. Updates selected task status to RUNNING
    5. Returns the first selected task
    """

    mock_monitor.get_available_ram_mb.return_value = 8096
    mock_monitor.get_available_cpu_cores.return_value = 4.0

    t_new = sample_task.model_copy(update={'task_id': 'new_1', 'status': TaskStatus.NEW})
    t_pending = sample_task.model_copy(update={'task_id': 'pending-1', 'status': TaskStatus.PENDING})

    mock_data_service.query_active_tasks.side_effect = [
        ([t_new], None),
        ([t_pending], None)
    ]

    # Lets say that the strategy picked the pending task t_pending
    mock_strategy.select_tasks.return_value = [t_pending]

    # Make the call to get_next_task()
    result_task = scheduler.get_next_task()

    # Check strategy was passed both NEW and PENDING tasks
    call_args = mock_strategy.select_tasks.call_args
    passed_kwargs = call_args[1]
    passed_tasks = passed_kwargs['pending_tasks']
    assert len(passed_tasks) == 2 # Both NEW and PENDING were passed

    # Check task was updated to RUNNING status
    assert mock_data_service.update_task.call_count == 1
    updated_arg = mock_data_service.update_task.call_args[0][0]
    assert updated_arg.task_id == "pending-1"
    assert updated_arg.status == TaskStatus.RUNNING

    assert result_task.task_id == 'pending-1'

def test_get_next_task_returns_none_if_strategy_selects_nothing(
        scheduler, mock_monitor, mock_strategy, mock_data_service
):
    """Tests that if strategy returns empty list, scheduler returns None."""
    mock_data_service.query_active_tasks.return_value = ([], None)
    mock_strategy.select_tasks.return_value = []

    assert scheduler.get_next_task() is None


