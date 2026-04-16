"""
Structured logging for EchoMind.
Provides consistent logging across all components with file and console output.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log files
MAIN_LOG_FILE = LOG_DIR / "echomind.log"
ERROR_LOG_FILE = LOG_DIR / "echomind_errors.log"
INGESTION_LOG_FILE = LOG_DIR / "ingestion.log"

# Format: timestamp | level | logger_name | message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """
    Setup structured logging for the entire EchoMind application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Main log file handler
    try:
        main_file_handler = logging.FileHandler(MAIN_LOG_FILE, mode='a', encoding='utf-8')
        main_file_handler.setLevel(numeric_level)
        main_file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        main_file_handler.setFormatter(main_file_formatter)
        root_logger.addHandler(main_file_handler)
    except Exception as e:
        print(f"Warning: Could not create main log file: {e}")
    
    # Error log file handler (WARNING and above)
    try:
        error_file_handler = logging.FileHandler(ERROR_LOG_FILE, mode='a', encoding='utf-8')
        error_file_handler.setLevel(logging.WARNING)
        error_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        error_file_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_file_handler)
    except Exception as e:
        print(f"Warning: Could not create error log file: {e}")
    
    # Create child loggers with prefixes
    root_logger.info(f"=" * 70)
    root_logger.info(f"EchoMind Logging Initialized - Level: {level}")
    root_logger.info(f"Main Log: {MAIN_LOG_FILE}")
    root_logger.info(f"Error Log: {ERROR_LOG_FILE}")
    root_logger.info(f"=" * 70)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper naming."""
    return logging.getLogger(name)


# Module-level convenience functions
def log_info(message: str, module: str = "EchoMind"):
    """Log an info message."""
    logger = get_logger(module)
    logger.info(message)


def log_warning(message: str, module: str = "EchoMind"):
    """Log a warning message."""
    logger = get_logger(module)
    logger.warning(message)


def log_error(message: str, module: str = "EchoMind"):
    """Log an error message."""
    logger = get_logger(module)
    logger.error(message)


def log_debug(message: str, module: str = "EchoMind"):
    """Log a debug message."""
    logger = get_logger(module)
    logger.debug(message)


# Setup logging on module import
setup_logging()
