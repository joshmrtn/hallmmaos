import pytest
import logging
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from src.utils.logging_utils import setup_logging
from src.config.config_manager import ConfigManager

@pytest.fixture
def mock_config():
    """Mocks the ConfigManager to return controlled settings."""
    with patch('src.utils.logging_utils.ConfigManager') as MockCM:
        instance = MockCM.instance.return_value
        
        # Default behavior: Return a dict that mimics the config structure
        def get_side_effect(section, key, default=None):
            defaults = {
                "system": {"log_level": "DEBUG"},
                "logging": {
                    "log_dir": "/tmp/mock_logs",
                    "log_file_name": "test.log",
                    "max_bytes": 1000,
                    "backup_count": 2
                },
                "tasks_data": {"data_base_dir": "/tmp/data"}
            }
            return defaults.get(section, {}).get(key, default)
            
        instance.get.side_effect = get_side_effect
        yield instance

@patch('src.utils.logging_utils.logging')
@patch('src.utils.logging_utils.sys')
def test_setup_logging_basic_configuration(mock_sys, mock_logging, mock_config):
    """
    Tests that setup_logging sets the correct level and adds a stream handler.
    """
    # Setup Mocks
    mock_root_logger = MagicMock()
    mock_root_logger.handlers = [] # Simulate empty handlers
    mock_logging.getLogger.return_value = mock_root_logger
    mock_logging.DEBUG = 10
    
    # ACT
    setup_logging()
    
    # ASSERT
    # 1. Check ConfigManager was consulted
    mock_config.get.assert_any_call("system", "log_level", "INFO")
    
    # 2. Check Level Set
    mock_root_logger.setLevel.assert_called_with(10) # DEBUG level
    
    # 3. Check StreamHandler (Console) added
    mock_logging.StreamHandler.assert_called_with(mock_sys.stdout)
    mock_root_logger.addHandler.assert_any_call(mock_logging.StreamHandler.return_value)

@patch('src.utils.logging_utils.logging.handlers.RotatingFileHandler')
@patch('src.utils.logging_utils.logging')
def test_setup_logging_creates_file_handler(mock_logging, mock_rfh, mock_config):
    """
    Tests that if log_dir is configured, a RotatingFileHandler is created.
    """
    mock_root_logger = MagicMock()
    mock_logging.getLogger.return_value = mock_root_logger
    
    # ACT
    setup_logging()
    
    # ASSERT
    # Check RotatingFileHandler initialization
    mock_rfh.assert_called_with(
        Path("/tmp/mock_logs/test.log"),
        maxBytes=1000,
        backupCount=2
    )
    
    # Check it was added to root logger
    mock_root_logger.addHandler.assert_any_call(mock_rfh.return_value)

@patch('src.utils.logging_utils.logging.handlers.RotatingFileHandler')
@patch('src.utils.logging_utils.logging')
def test_setup_logging_handles_file_permission_error(mock_logging, mock_rfh, mock_config):
    """
    Tests that if file logging fails (e.g. permission denied), 
    the app prints a warning but DOES NOT CRASH.
    """
    mock_root_logger = MagicMock()
    mock_logging.getLogger.return_value = mock_root_logger
    
    # Simulate PermissionError when trying to create the file handler
    mock_rfh.side_effect = PermissionError("Access Denied")
    
    # ACT
    try:
        setup_logging()
    except Exception as e:
        pytest.fail(f"setup_logging crashed on permission error: {e}")
        
    # ASSERT
    # StreamHandler should still be added even if FileHandler failed
    mock_logging.StreamHandler.assert_called()
    
    # FileHandler should have been attempted
    mock_rfh.assert_called()
