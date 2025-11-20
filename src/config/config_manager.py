import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

from platformdirs import site_config_dir, user_log_dir
import inspect

import logging

logger = logging.getLogger(__name__)

APP_NAME = "hallmmaos"
CONFIG_FILE_NAME = "config.json"
DEFAULT_FILE_NAME = "default_config.yaml"

class ConfigManager:
    """
    Manages loading and accessing application configuration, implementing the 
    Singleton pattern to ensure the file is loaded only once.
    """
    _instance: Optional['ConfigManager'] = None
    _config_data: Dict[str, Any] = {}
    _default_config_data: Dict[str, Any] = {}


    def __new__(cls, *args, **kwargs):
        """Ensures only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_defaults()
            cls._instance._load_config()
        return cls._instance
    

    def _get_app_config_path(self) -> Path:
        """Determines the standard, OS-specific path for user's config file."""
        config_dir = Path(site_config_dir(appname=APP_NAME))
        return config_dir / CONFIG_FILE_NAME
    

    def _get_default_file_path(self) -> Path:
        """Determines the path to the internal default_config.yaml file."""
        current_file_dir = Path(inspect.getfile(self.__class__)).parent
        return current_file_dir / "defaults" / DEFAULT_FILE_NAME
    

    def _get_data_base_dir(self) -> Path:
        """
        Helper function to calculate OS-appropriate path for local data files.

        Used by _write_default_config to fill in the "data_base_dir" config variable.

        Returns:
            The Path object representing the OS specific path where local data 
            files will live in a default configuration.
        """
        return Path(site_config_dir(appname=APP_NAME)).parent.joinpath("data")

    def _get_log_base_dir(self) -> Path:
        """
        Calculates the OS-appropriate directory for logs.
        """
        return Path(user_log_dir(appname=APP_NAME))

    def _load_defaults(self) -> None:
        """Loads the default configuration from the internal default_config.yaml file."""
        default_path = self._get_default_file_path()
        try:
            with open(default_path, 'r') as f:
                ConfigManager._default_config_data = yaml.safe_load(f)
            logger.info(f"Loaded default configuration from : {default_path}")
        except (IOError, yaml.YAMLError) as e:
            logger.critical(f"Failed to load application defaults from {default_path}: {e}", exc_info=True)
            raise RuntimeError(f"FATAL: Failed to load application defaults from {default_path}: {e}")

    def _write_default_config(self, config_path: Path) -> None: 
        """Writes the default configuration to the specified path."""

        writeable_config = self._default_config_data.copy()
        calculated_data_path = self._get_data_base_dir().as_posix()
        calculated_log_path = self._get_log_base_dir().as_posix()

        if writeable_config.get("tasks_data", {}).get("data_base_dir") == "__CALCULATE_DATA_PATH__":
             writeable_config["tasks_data"]["data_base_dir"] = calculated_data_path

        if writeable_config.get("logging", {}).get("log_dir") == "__CALCULATE_LOG_PATH__":
            writeable_config["logging"]["log_dir"] = calculated_log_path
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                yaml.dump(writeable_config, f, indent=2, sort_keys=False)

            logger.info(f"Created default configuration file at: {config_path}")
        except IOError as e:
            logger.error(f"Failed to write default configuration to disk: {e}", exc_info=True)
            raise RuntimeError(f"Failed to write default configuration to disk: {e}")
    

    def _load_config(self) -> None:
        """Loads configuration from the file into the internal dictionary."""
        config_path = self._get_app_config_path()

        if not config_path.exists():
            logger.warning(f"Configuration file not found at {config_path}. Writing default config.")
            self._write_default_config(config_path)
            

        try:
            with open(config_path, 'r') as f:
                ConfigManager._config_data = yaml.safe_load(f)
        except (IOError, yaml.YAMLError) as e:
            logger.error(f"ERROR: Error loading configuration from {config_path}: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize configuration from {config_path}: {e}")
        

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by section and key."""

        # Try to get value from the user's loaded configuration.
        user_value = ConfigManager._config_data.get(section, {}).get(key)
        if user_value is not None:
            return user_value
        
        # Fall back to default configuration if not found in user configuration.
        default_value = ConfigManager._default_config_data.get(section, {}).get(key)
        if default_value is not None:
            return default_value
        
        # Fall back to passed-in default value if neither found.
        return default
    
    @staticmethod
    def instance() -> 'ConfigManager':
        """Returns the single instance of the ConfigManager."""
        if ConfigManager._instance is None:
            ConfigManager()
        return ConfigManager._instance