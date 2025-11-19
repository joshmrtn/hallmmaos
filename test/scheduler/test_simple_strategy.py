import pytest
from unittest.mock import MagicMock, create_autospec
from datetime import datetime, timedelta
from src.scheduler.simple_strategy import SimpleSchedulingStrategy
from src.services.task_data_service import TaskDataService
from src.models.task_types import Task, TaskStatus

# --- Fixtures ---

@pytest.fixture
def mock_data_service():
    return create_autospec(TaskDataService, instance=True)

@pytest.fixture
def strategy(mock_data_service):
    return SimpleSchedulingStrategy(data_service=mock_data_service)

@pytest.fixture
def base_task():
    """Helper to create tasks."""
    def _create(task_id, priority=5, blocked_by=None, status=TaskStatus.PENDING):
        return Task(
            task_id=task_id,
            agent_id="agent-1",
            source_domain='test',
            source_topic='test',
            input_message='data',
            priority=priority,
            status=status,
            blocked_by=blocked_by or []
        )
    return _create


# --- Tests ---

def test_select_tasks_filters_blocked_tasks(strategy, mock_data_service, base_task):
    """
    Sets up the scenario:
    Task A blocked by Task B
    Task B is running
    Task C has no dependencies

    Expected: Returns only Task C
    """
    task_a = base_task("A", blocked_by=["B"])
    task_c = base_task("C")
    task_b_stub = base_task("B", status=TaskStatus.RUNNING)
    mock_data_service.get_task_by_id.side_effect = lambda tid: task_b_stub if tid == "B" else None

    result = strategy.select_tasks([task_a, task_c], 1000, 4.0)

    assert len(result) == 1
    assert result[0].task_id == "C"

def test_select_tasks_allows_tasks_with_completed_dependencies(strategy, mock_data_service, base_task):
    """
    Sets up the scenario:
    Task A blocked by Task B
    Task B status is COMPLETED (non-blocking)

    Expected to return Task A.
    """
    task_a = base_task("A", blocked_by=["B"])
    task_b_stub = base_task("B", status=TaskStatus.COMPLETED)
    mock_data_service.get_task_by_id.return_value = task_b_stub

    result = strategy.select_tasks([task_a], 1000, 4.0)

    assert len(result) == 1
    assert result[0].task_id == "A"


def test_select_tasks_allows_tasks_with_missing_dependencies(strategy, mock_data_service, base_task):
    """
    Scenario: Task A blocked by Task B, but B does not exist in DB (deleted)
    
    Expected to return Task A as non-blocked
    """
    task_a = base_task("A", blocked_by=["B"])
    mock_data_service.get_task_by_id.return_value = None # Task B not found

    result = strategy.select_tasks([task_a], 1000, 4.0)

    assert len(result) == 1
    assert result[0].task_id == "A"


def test_select_tasks_sorts_by_priority_and_creation(strategy, mock_data_service, base_task):
    """
    Scenario: 3 tasks with different priorities and creation times.
    T1: Priority 10, created now
    T2: Priority 1, created now
    T3: Priority 1, created earlier (older)
    Expected order: T3, T2, T1
    """

    now = datetime.now()
    earlier = now - timedelta(minutes=10)

    t1 = base_task("T1", priority=10)
    t2 = base_task("T2", priority=1)
    t3 = base_task("T3", priority=1).model_copy(update={'created_at': earlier})

    result = strategy.select_tasks([t1, t2, t3], 1000, 4.0)

    assert len(result) == 3
    assert result[0].task_id == "T3"
    assert result[1].task_id == "T2"
    assert result[2].task_id == "T1"

def test_select_tasks_respects_limit(strategy, mock_data_service, base_task):
    """Tests that strategy cuts off list at 10 items (hardcoded in SimpleStrategy)"""
    tasks = []
    for i in range(15):
        tasks.append(base_task(str(i)))
    result = strategy.select_tasks(tasks, 1000, 4.0)

    assert len(result) == 10