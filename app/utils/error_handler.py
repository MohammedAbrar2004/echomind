"""
Error handling and retry logic for EchoMind ingestion pipeline.
Centralizes error tracking and exponential backoff retry strategy.
"""

import logging
import time
from datetime import datetime
from typing import Callable, Any, TypeVar, Optional
from functools import wraps

logger = logging.getLogger("EchoMind.ErrorHandler")

T = TypeVar('T')

# Error severity tracking
TRANSIENT_ERRORS = (
    ConnectionError,
    TimeoutError,
    BrokenPipeError,
    ConnectionResetError,
    ConnectionAbortedError,
)

PERMANENT_ERRORS = (
    FileNotFoundError,
    PermissionError,
    ValueError,
)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay_seconds: float = 1,
        max_delay_seconds: float = 60,
        exponential_base: float = 2.0,
        backoff_jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay_seconds: Initial delay between retries
            max_delay_seconds: Maximum delay between retries
            exponential_base: Base for exponential backoff
            backoff_jitter: Whether to add random jitter to delay
        """
        self.max_retries = max_retries
        self.initial_delay_seconds = initial_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.exponential_base = exponential_base
        self.backoff_jitter = backoff_jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = min(
            self.initial_delay_seconds * (self.exponential_base ** attempt),
            self.max_delay_seconds
        )
        
        if self.backoff_jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay


def retry_with_backoff(config: Optional[RetryConfig] = None) -> Callable:
    """
    Decorator for functions that should retry with exponential backoff.
    
    Usage:
        @retry_with_backoff()
        def fetch_something():
            ...
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except PERMANENT_ERRORS as e:
                    # Don't retry permanent errors
                    logger.error(f"{func.__name__}: Permanent error (no retry): {e}")
                    raise
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"{func.__name__}: Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__}: All {config.max_retries + 1} attempts failed: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator


class IngestionError:
    """Represents an error that occurred during ingestion."""
    
    def __init__(
        self,
        source_type: str,
        external_message_id: str,
        error_message: str,
        error_type: str,
        retry_count: int = 0,
        is_permanent: bool = False
    ):
        self.source_type = source_type
        self.external_message_id = external_message_id
        self.error_message = error_message
        self.error_type = error_type
        self.retry_count = retry_count
        self.is_permanent = is_permanent
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/DB storage."""
        return {
            "source_type": self.source_type,
            "external_message_id": self.external_message_id,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "retry_count": self.retry_count,
            "is_permanent": self.is_permanent,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        return (
            f"[{self.error_type}] {self.source_type}/{self.external_message_id}: "
            f"{self.error_message} (retries: {self.retry_count})"
        )


class ErrorTracker:
    """Tracks errors during ingestion for reporting and retry."""
    
    def __init__(self):
        self.errors: list[IngestionError] = []
        self.by_source: dict[str, list[IngestionError]] = {}
    
    def add_error(self, error: IngestionError):
        """Add an error to tracking."""
        self.errors.append(error)
        
        if error.source_type not in self.by_source:
            self.by_source[error.source_type] = []
        self.by_source[error.source_type].append(error)
    
    def get_retryable_errors(self) -> list[IngestionError]:
        """Get all non-permanent errors that can be retried."""
        return [e for e in self.errors if not e.is_permanent]
    
    def get_permanent_errors(self) -> list[IngestionError]:
        """Get all permanent errors."""
        return [e for e in self.errors if e.is_permanent]
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        retryable = self.get_retryable_errors()
        permanent = self.get_permanent_errors()
        
        return {
            "total_errors": len(self.errors),
            "retryable_errors": len(retryable),
            "permanent_errors": len(permanent),
            "by_source": {
                source: len(errors)
                for source, errors in self.by_source.items()
            }
        }
    
    def log_summary(self):
        """Log error summary."""
        summary = self.get_summary()
        
        if summary["total_errors"] == 0:
            logger.info("ErrorTracker: No errors recorded ✓")
            return
        
        logger.warning(
            f"ErrorTracker Summary:\n"
            f"  Total Errors: {summary['total_errors']}\n"
            f"  Retryable: {summary['retryable_errors']}\n"
            f"  Permanent: {summary['permanent_errors']}\n"
            f"  By Source: {summary['by_source']}"
        )


def classify_error(exception: Exception) -> tuple[bool, str]:
    """
    Classify an exception as transient or permanent.
    
    Returns:
        tuple: (is_permanent, error_type_str)
    """
    error_type = type(exception).__name__
    
    if isinstance(exception, PERMANENT_ERRORS):
        return True, error_type
    
    if isinstance(exception, TRANSIENT_ERRORS):
        return False, error_type
    
    # Default: treat most exceptions as transient/retryable
    return False, error_type
