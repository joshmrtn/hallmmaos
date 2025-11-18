import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.models.task_types import Task, TaskStatus
from src.data.json_task_repository import JsonTaskRepository
from typing import List

# --- Fixtures ---

@pytest.fixture
def sample_task_data():
    """Returns a factory function to create Task instances with unique IDs."""
    base_time = datetime.now()
    def _create_task(
        task_id: str, 
        status: TaskStatus = TaskStatus.NEW, 
        priority: int = 5,
        created_at_offset_sec: int = 0,
        correlation_ids: List[str] = None
    ) -> Task:
        return Task(
            task_id=task_id,
            agent_id=f"agent-{task_id}",
            source_domain="test.domain",
            source_topic="test_topic",
            input_message=f"Test message for {task_id}",
            priority=priority,
            blocked_by=[],
            blocking=[],
            correlation_ids=correlation_ids or [],
            status=status,
            created_at=base_time + timedelta(seconds=created_at_offset_sec)
        )
    return _create_task

@pytest.fixture
def json_repo(tmp_path: Path, sample_task_data):
    """
    Creates a JsonTaskRepository instance backed by a temporary file.
    Also pre-loads some tasks for querying tests.
    """
    file_path = tmp_path / "tasks_test.json"
    repo = JsonTaskRepository(file_path)

    # Pre-load tasks for query testing
    repo.add(sample_task_data("t1", TaskStatus.PENDING, priority=1, created_at_offset_sec=10, correlation_ids=["proj-A"]))
    repo.add(sample_task_data("t2", TaskStatus.RUNNING, priority=5, created_at_offset_sec=20, correlation_ids=["proj-A", "user-X"]))
    repo.add(sample_task_data("t3", TaskStatus.PENDING, priority=10, created_at_offset_sec=30, correlation_ids=["proj-B"]))
    repo.add(sample_task_data("t4", TaskStatus.COMPLETED, priority=3, created_at_offset_sec=40, correlation_ids=["proj-A"]))
    repo.add(sample_task_data("t5", TaskStatus.NEW, priority=7, created_at_offset_sec=50))
    
    # Reload to ensure persistence is working and in-memory is correct
    return JsonTaskRepository(file_path)

# --- Tests ---

def test_repo_initializes_with_empty_file(tmp_path: Path):
    """Tests that the repository starts empty if the file doesn't exist."""
    file_path = tmp_path / "new_tasks.json"
    repo = JsonTaskRepository(file_path)
    assert repo._tasks == {}
    assert not file_path.exists()

def test_repo_add_and_persistence(tmp_path: Path, sample_task_data):
    """Tests adding a task and verifying it's saved to the file."""
    file_path = tmp_path / "add_test.json"
    task = sample_task_data("add1")
    
    repo = JsonTaskRepository(file_path)
    repo.add(task)
    
    # Assert in-memory state
    assert repo.get_by_id("add1") == task
    
    # Assert persistence by reloading
    reloaded_repo = JsonTaskRepository(file_path)
    reloaded_task = reloaded_repo.get_by_id("add1")
    assert reloaded_task is not None
    assert reloaded_task.task_id == "add1"
    assert reloaded_task.status == TaskStatus.NEW
    
def test_repo_add_duplicate_raises_error(json_repo, sample_task_data):
    """Tests that adding a task with a duplicate ID raises a ValueError."""
    task = sample_task_data("t1")
    with pytest.raises(ValueError):
        json_repo.add(task)

def test_repo_update_task(json_repo, sample_task_data):
    """Tests updating an existing task."""
    original_task = json_repo.get_by_id("t1")
    
    # Create an updated task instance
    updated_task = original_task.model_copy(update={
        "status": TaskStatus.RUNNING, 
        "priority": 9
    })
    
    json_repo.update(updated_task)
    
    # Assert update in-memory
    retrieved_task = json_repo.get_by_id("t1")
    assert retrieved_task.status == TaskStatus.RUNNING
    assert retrieved_task.priority == 9
    
    # Assert persistence by reloading
    reloaded_repo = JsonTaskRepository(json_repo._file_path)
    reloaded_task = reloaded_repo.get_by_id("t1")
    assert reloaded_task.status == TaskStatus.RUNNING
    
def test_repo_update_nonexistent_task_raises_error(json_repo, sample_task_data):
    """Tests that updating a nonexistent task raises a KeyError."""
    nonexistent_task = sample_task_data("nonexistent")
    with pytest.raises(KeyError):
        json_repo.update(nonexistent_task)

def test_repo_delete_task(json_repo):
    """Tests deleting a task."""
    json_repo.delete_by_id("t2")
    
    # Assert delete in-memory
    assert json_repo.get_by_id("t2") is None
    
    # Assert persistence by reloading
    reloaded_repo = JsonTaskRepository(json_repo._file_path)
    assert reloaded_repo.get_by_id("t2") is None

def test_repo_delete_nonexistent_task_is_safe(json_repo):
    """Tests that deleting a nonexistent task does not raise an error."""
    try:
        json_repo.delete_by_id("nonexistent")
    except Exception as e:
        pytest.fail(f"Deleting nonexistent task raised unexpected error: {e}")

def test_repo_get_pending_count(json_repo):
    """Tests the method to count PENDING tasks."""
    # Tasks t1 (PENDING) and t3 (PENDING) should be counted
    assert json_repo.get_pending_count() == 2

# --- Query Tests ---

def test_repo_query_no_filters_returns_all_and_sorts_by_default(json_repo):
    """Tests query with no filters, returning all tasks sorted by created_at."""
    tasks, next_key = json_repo.query(limit=5)
    
    assert len(tasks) == 5
    assert next_key is None # All 5 tasks returned
    # Check default sort (created_at ascending)
    assert tasks[0].task_id == "t1" # created_at_offset_sec=10
    assert tasks[-1].task_id == "t5" # created_at_offset_sec=50

def test_repo_query_filter_by_status(json_repo):
    """Tests filtering by TaskStatus."""
    tasks, _ = json_repo.query(filter_status=TaskStatus.PENDING, limit=10)
    
    assert len(tasks) == 2
    assert {t.task_id for t in tasks} == {"t1", "t3"}

def test_repo_query_filter_by_correlation_id(json_repo):
    """Tests filtering by a correlation ID present in multiple tasks."""
    tasks, _ = json_repo.query(filter_correlation_id="proj-A", limit=10)
    
    assert len(tasks) == 3
    assert {t.task_id for t in tasks} == {"t1", "t2", "t4"}

def test_repo_query_sorting(json_repo):
    """Tests custom sorting by priority descending."""
    tasks, _ = json_repo.query(sort_field='priority', sort_ascending=False, limit=10)
    
    assert len(tasks) == 5
    # t3 (P10) -> t5 (P7) -> t2 (P5) -> t4 (P3) -> t1 (P1)
    assert tasks[0].task_id == "t3"
    assert tasks[-1].task_id == "t1"

def test_repo_query_pagination(json_repo):
    """Tests the pagination logic using limit and exclusive_start_key."""
    
    # 1. Get first page (limit=2, default sort is created_at asc)
    page1, next_key1 = json_repo.query(limit=2)
    assert len(page1) == 2
    assert {t.task_id for t in page1} == {"t1", "t2"}
    assert next_key1 == {'last_id': 't2'}

    # 2. Get second page
    page2, next_key2 = json_repo.query(limit=2, exclusive_start_key=next_key1)
    assert len(page2) == 2
    assert {t.task_id for t in page2} == {"t3", "t4"}
    assert next_key2 == {'last_id': 't4'}
    
    # 3. Get last page
    page3, next_key3 = json_repo.query(limit=2, exclusive_start_key=next_key2)
    assert len(page3) == 1
    assert {t.task_id for t in page3} == {"t5"}
    assert next_key3 is None # End of results

def test_repo_query_pagination_with_filter(json_repo):
    """Tests pagination combined with filtering (PENDING tasks: t1, t3)."""
    
    # 1. Get first page (limit=1, filter=PENDING)
    page1, next_key1 = json_repo.query(limit=1, filter_status=TaskStatus.PENDING)
    assert len(page1) == 1
    assert page1[0].task_id == "t1"
    assert next_key1 == {'last_id': 't1'}

    # 2. Get second page
    page2, next_key2 = json_repo.query(limit=1, filter_status=TaskStatus.PENDING, exclusive_start_key=next_key1)
    assert len(page2) == 1
    assert page2[0].task_id == "t3"
    assert next_key2 is None