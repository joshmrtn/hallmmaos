import logging
import logging.handlers
from pathlib import Path
import sys
from src.config.config_manager import ConfigManager

def setup_logging():
    """
    Configures root logger based on application settings.
    Should be called once in main.py before other modules start working.
    """
    config = ConfigManager.instance()

    # Get log level from application config.
    log_level_str = config.get("system", "log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Set up logging format.
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicates.
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler.
    try:
        # Use configured log directory.
        log_dir_str = config.get("logging", "log_dir")
        file_name = config.get("logging", "log_file_name", "hallmmaos.log")
        max_bytes = config.get("logging", "max_bytes", 10485760) # 10MB
        backup_count = config.get("logging", "backup_count", 5)

        if log_dir_str:
            log_dir = Path(log_dir_str)
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / file_name

            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )

            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            logging.info(f"File logging enabled: {log_file}")

    except Exception as e:
        # Failing to write logs shouldn't crash the system.
        print(f"WARNING: Failed to setup file logging: {e}", file=sys.stderr)

    logging.info(f"Logging initialized. Level: {log_level_str}")