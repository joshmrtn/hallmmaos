import pytest
from unittest.mock import MagicMock, create_autospec
from pathlib import Path
from datetime import datetime, timedelta 
from typing import List, Optional, Dict, Any

from src.models.task_types import Task, TaskStatus
from src.data.json_task_repository import JsonTaskRepository 
from src.data.base_task_repository import BaseTaskRepository
from src.config.config_manager import ConfigManager
from src.services.task_data_service import TaskDataService

# --- Fixtures ---

@pytest.fixture
def mock_config_manager(tmp_path):
    """Mocks the ConfigManager instance to return valid configuration."""
    mock_config = create_autospec(ConfigManager, instance=True)
    
    # Define the mock configuration data using tmp_path
    mock_config_data = {
        "tasks_data": {
            "data_base_dir": str(tmp_path / "test_data_service"), 
            "active_repo_file": "active.json",
            "archive_repo_file": "archive.json",
        }
    }
    
    # Configure the 'get' method of the mock ConfigManager
    # This handles the call: config_manager.get("tasks_data", {})
    def get_side_effect(section, default=None):
        return mock_config_data.get(section, default)
    
    mock_config.get.side_effect = get_side_effect
    return mock_config

@pytest.fixture
def setup_repos(tmp_path):
    """
    Sets up two real JsonTaskRepository instances backed by temporary files 
    for isolated testing of TaskDataService interaction logic.
    """
    base_dir = tmp_path / "test_data_service"
    active_path = base_dir / "active.json"
    archive_path = base_dir / "archive.json"
    
    active_repo = JsonTaskRepository(active_path)
    archive_repo = JsonTaskRepository(archive_path)
    
    return active_repo, archive_repo

@pytest.fixture
def task_data_service(mock_config_manager, setup_repos, monkeypatch):
    """
    Initializes the TaskDataService by monkeypatching __init__ to inject 
    the real, file-backed repositories, bypassing the complex setup.
    """
    active_repo, archive_repo = setup_repos

    # Define the mock __init__ function
    def mock_init_repos(self, config_manager):
        # We perform the config lookups to satisfy the logic flow of the original __init__
        repo_config = config_manager.get("tasks_data", {})
        base_data_dir = repo_config.get("data_base_dir")
        base_path = Path(base_data_dir or "/tmp/dummy")

        self._config = config_manager
        self._active_repo = active_repo
        self._archive_repo = archive_repo
        
    # Apply the monkeypatch to TaskDataService.__init__
    monkeypatch.setattr(TaskDataService, "__init__", mock_init_repos)
    
    # Create the service, which calls our mocked __init__
    service = TaskDataService(mock_config_manager)
    return service

@pytest.fixture
def mock_task():
    """Returns a minimal, valid Task object."""
    return Task(
        task_id="TID-123",
        agent_id="A-001",
        source_domain="test.com",
        source_topic="topic",
        input_message="Do work",
        priority=5,
        blocked_by=[],
        blocking=[],
        correlation_ids=["P-ABC"]
    )

@pytest.fixture
def sample_task_data():
    """Returns a factory function to create Task instances for query testing."""
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


# --- Tests ---

def test_service_initialization_failure(tmp_path):
    """
    Tests initialization fails if a critical config key ('data_base_dir') is missing.
    Requires a separate mock that returns an empty config dictionary.
    """
    failing_mock_config = create_autospec(ConfigManager, instance=True)
    # The config manager must return an empty dict for "tasks_data" to test the ValueError path
    failing_mock_config.get.side_effect = lambda section, default=None: (
        {} if section == "tasks_data" else default
    )
    
    # The TaskDataService's original __init__ logic is executed here
    with pytest.raises(ValueError, match="data_base_dir"):
        TaskDataService(failing_mock_config)


def test_service_add_task_success(task_data_service, mock_task):
    """Tests adding a NEW task goes to the active repo."""
    task = mock_task.model_copy(update={"status": TaskStatus.NEW}) 
    
    task_data_service.add_task(task)
    
    assert task_data_service._active_repo.get_by_id(task.task_id) is not None
    assert task_data_service._archive_repo.get_by_id(task.task_id) is None

def test_service_add_task_wrong_status_fails(task_data_service, mock_task):
    """Tests adding a task with non-NEW status raises an error."""
    task = mock_task.model_copy(update={"status": TaskStatus.PENDING}) 
    with pytest.raises(ValueError):
        task_data_service.add_task(task)

def test_service_get_task_by_id_active_priority(task_data_service, mock_task):
    """Tests get_task_by_id retrieves from Active repo first."""
    task_data_service._active_repo.add(mock_task)
    
    retrieved_task = task_data_service.get_task_by_id(mock_task.task_id)
    assert retrieved_task is not None
    assert retrieved_task.task_id == mock_task.task_id

def test_service_get_task_by_id_archive_fallback(task_data_service, mock_task):
    """Tests get_task_by_id retrieves from Archive repo as a fallback."""
    task_data_service._archive_repo.add(mock_task)
    
    retrieved_task = task_data_service.get_task_by_id(mock_task.task_id)
    assert retrieved_task is not None

def test_service_update_task_active_to_archive_move(task_data_service, mock_task):
    """Tests status change from PENDING to COMPLETED triggers Active -> Archive move."""
    # 1. Start in Active Repo
    active_task = mock_task.model_copy(update={"status": TaskStatus.PENDING})
    task_data_service._active_repo.add(active_task)
    
    # 2. Update status and trigger move
    archived_task = active_task.model_copy(update={"status": TaskStatus.COMPLETED})
    task_data_service.update_task(archived_task)
    
    # 3. Assert move completed
    assert task_data_service._active_repo.get_by_id(active_task.task_id) is None
    assert task_data_service._archive_repo.get_by_id(active_task.task_id).status == TaskStatus.COMPLETED

def test_service_update_task_archive_to_active_move(task_data_service, mock_task):
    """Tests status change from FAILED to PENDING triggers Archive -> Active move (re-queue)."""
    # 1. Start in Archive Repo
    archived_task = mock_task.model_copy(update={"status": TaskStatus.FAILED})
    task_data_service._archive_repo.add(archived_task)
    
    # 2. Update status and trigger move
    active_task = archived_task.model_copy(update={"status": TaskStatus.PENDING, "priority": 1})
    task_data_service.update_task(active_task)
    
    # 3. Assert move completed
    assert task_data_service._archive_repo.get_by_id(archived_task.task_id) is None
    assert task_data_service._active_repo.get_by_id(archived_task.task_id).status == TaskStatus.PENDING
    assert task_data_service._active_repo.get_by_id(archived_task.task_id).priority == 1

def test_service_update_task_in_place_active(task_data_service, mock_task):
    """Tests updating a field (like priority) of an active task without moving it."""
    # 1. Start and stay in Active Repo (PENDING -> PENDING)
    original_task = mock_task.model_copy(update={"status": TaskStatus.PENDING, "priority": 5})
    task_data_service._active_repo.add(original_task)
    
    # 2. Update priority
    updated_task = original_task.model_copy(update={"priority": 1})
    task_data_service.update_task(updated_task)
    
    # 3. Assert updated in Active, not moved
    assert task_data_service._active_repo.get_by_id(original_task.task_id).priority == 1
    assert task_data_service._archive_repo.get_by_id(original_task.task_id) is None

def test_service_query_all_tasks_combines_active_and_archive(task_data_service, mock_task, sample_task_data):
    """Tests query_all_tasks successfully combines and limits results from both repos."""
    
    # ARRANGE: Add 2 Active tasks (t_a1, t_a2) and 2 Archive tasks (t_r3, t_r4)
    # Tasks are created with increasing created_at_offset_sec for predictable sorting
    active1 = sample_task_data("t_a1", TaskStatus.PENDING, created_at_offset_sec=10, correlation_ids=["group1"])
    active2 = sample_task_data("t_a2", TaskStatus.RUNNING, created_at_offset_sec=20, correlation_ids=["group1"])
    archive3 = sample_task_data("t_r3", TaskStatus.COMPLETED, created_at_offset_sec=30, correlation_ids=["group1"])
    archive4 = sample_task_data("t_r4", TaskStatus.FAILED, created_at_offset_sec=40)
    
    task_data_service._active_repo.add(active1)
    task_data_service._active_repo.add(active2)
    task_data_service._archive_repo.add(archive3)
    task_data_service._archive_repo.add(archive4)
    
    # ACT 1: Query all with a limit of 3. (Should get all 2 active + 1 archive, sorted by created_at)
    tasks, next_key = task_data_service.query_all_tasks(limit=3)
    
    # ASSERT 1
    assert len(tasks) == 3
    # Order should be t_a1, t_a2, t_r3 (by created_at)
    assert [t.task_id for t in tasks] == ["t_a1", "t_a2", "t_r3"]
    # Since the first 3 items were found, and t_r4 exists, the next key should point to archive's next item
    # The pagination logic for the archive repo returns the last ID of the page if more exist
    assert next_key == {'last_id': 't_r3'} 
    
    # ACT 2: Query the next page using the cursor
    tasks_page2, next_key_page2 = task_data_service.query_all_tasks(limit=3, exclusive_start_key=next_key)

    # ASSERT 2
    assert len(tasks_page2) == 1
    assert tasks_page2[0].task_id == "t_r4"
    assert next_key_page2 is None # End of results

    # ACT 3: Test filtering by correlation_id across both repos (group1)
    tasks_filtered, _ = task_data_service.query_all_tasks(filter_correlation_id="group1", limit=10)

    # ASSERT 3
    assert len(tasks_filtered) == 3
    assert {t.task_id for t in tasks_filtered} == {"t_a1", "t_a2", "t_r3"}