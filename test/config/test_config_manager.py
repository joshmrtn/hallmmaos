from pathlib import Path
import pytest
import yaml
import os

# Assume your package structure allows this import:
from src.config.config_manager import ConfigManager, APP_NAME, CONFIG_FILE_NAME 

# ------------------- Test Fixtures -------------------

@pytest.fixture(scope="function")
def fake_config_path(tmp_path, monkeypatch):
    """
    Mocks platformdirs to use a temporary directory for configuration files 
    and ensures the ConfigManager singleton is reset before each test.
    """
    
    # 1. Mock platformdirs to return our temporary path
    # We replace the actual site_config_dir function with one that returns tmp_path
    def mock_site_config_dir(appname, *args, **kwargs):
        # We also create the expected 'hallmmaos' subdirectory for completeness
        config_dir = tmp_path / 'mock_config_root' / APP_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir)
    
    def mock_user_log_dir(appname, *args, **kwargs):
        log_dir = tmp_path / 'mock_log_root' / APP_NAME
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir)

    monkeypatch.setattr(
        'src.config.config_manager.site_config_dir', 
        mock_site_config_dir
    )
    monkeypatch.setattr(
        'src.config.config_manager.user_log_dir',
        mock_user_log_dir
    )
    
    # 2. Clear the Singleton instance before each test
    # This is CRITICAL for testing Singletons like ConfigManager
    ConfigManager._instance = None
    
    # 3. Yield the path to the main config file for the test function to use
    yield tmp_path / 'mock_config_root' / APP_NAME / CONFIG_FILE_NAME
    
    # 4. Ensure the singleton is cleared again after the test (just in case)
    ConfigManager._instance = None

# ------------------- Test Cases -------------------

def test_config_manager_creates_default_file_when_missing(fake_config_path):
    """
    Tests that if config.yaml does not exist, the ConfigManager creates it
    using the embedded defaults and the correct OS path.
    """
    # ASSERT initial state: File should NOT exist at the mocked path
    assert not fake_config_path.exists()
    
    # ACT: Initialize the manager (this should trigger file creation)
    manager = ConfigManager()
    
    # ASSERT final state: File must exist now
    assert fake_config_path.exists()
    
    # ACT: Load the created file's content
    with open(fake_config_path, 'r') as f:
        config_content = yaml.safe_load(f)
        
    # ASSERT: Check for a known default key
    assert config_content['system']['log_level'] == 'INFO'
    
    # ASSERT: Check that the placeholder was replaced with a real OS path
    data_dir = config_content['tasks_data']['data_base_dir']
    assert data_dir.startswith(os.sep) or data_dir.startswith('C:') # Check for standard path start
    assert '__CALCULATE_DATA_PATH__' not in data_dir

    # ASSERT: Check Log Dir Path calculation
    log_dir = config_content['logging']['log_dir']
    assert '__CALCULATE_LOG_PATH__' not in log_dir
    assert 'mock_log_root' in log_dir

def test_config_manager_reads_custom_file_and_ignores_defaults(fake_config_path):
    """
    Tests that if config.yaml exists, the ConfigManager reads it and uses its custom values.
    """
    # ARRANGE: Write a custom config file that deviates from defaults
    custom_content = {
        'system': {'log_level': 'DEBUG'},
        'tasks_data': {'active_repo_file': 'custom_active.json'},
        'logging': {'log_dir': '/custom/logs'}
    }
    
    # Ensure the parent directory exists before writing the file
    fake_config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fake_config_path, 'w') as f:
        yaml.dump(custom_content, f)

    # ACT: Initialize the manager
    manager = ConfigManager()

    # ASSERT: Manager uses the custom value, not the default ('INFO')
    assert manager.get('system', 'log_level') == 'DEBUG'
    # ASSERT: Manager uses custom logging path value
    assert manager.get('logging', 'log_dir') == '/custom/logs'
    # ASSERT: Manager uses the custom value
    assert manager.get('tasks_data', 'active_repo_file') == 'custom_active.json'
    # ASSERT: Manager falls back to default for keys not specified (e.g., shutdown_timeout_sec)
    assert manager.get('system', 'shutdown_timeout_sec') == 30

def test_config_manager_is_a_singleton(fake_config_path):
    """Tests that subsequent calls return the exact same instance."""
    
    # ACT
    manager1 = ConfigManager()
    manager2 = ConfigManager()
    
    # ASSERT
    assert manager1 is manager2
    
def test_config_manager_handles_missing_keys():
    """Tests fallback logic."""
    manager = ConfigManager() # Loads defaults
    
    # ASSERT: Missing section returns None
    assert manager.get('non_existent_section', 'key', default=None) is None
    # ASSERT: Missing key in existent section returns the supplied default
    assert manager.get('system', 'missing_key', default='FALLBACK') == 'FALLBACK'