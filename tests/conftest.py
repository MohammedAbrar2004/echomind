"""
Shared pytest configuration and fixtures for all tests.
"""

import pytest
import time
import os
from unittest.mock import MagicMock, patch


@pytest.fixture
def benchmark():
    """
    Custom benchmark fixture that runs function multiple times and returns stats.
    
    Returns:
        dict: Contains timing information (min, max, avg, iterations)
    """
    def _benchmark(func, *args, number=5, repeat=1, **kwargs):
        """
        Run a function and collect timing statistics.
        
        Args:
            func: Callable to benchmark
            number: Number of times to call the function per iteration
            repeat: Number of iterations to run
        
        Returns:
            dict: Timing statistics
        """
        times = []
        for _ in range(repeat):
            start = time.perf_counter()
            for _ in range(number):
                func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            times.append(elapsed / number)
        
        return {
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'iterations': len(times),
            'unit': 'seconds'
        }
    
    return _benchmark


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def sample_memory_chunk_data():
    """Sample data for memory chunk insertion tests."""
    return {
        "user_id": "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9",
        "source_id": "39218ef4-b3ce-4b98-b1e2-34afa243c785",
        "external_message_id": "msg_123",
        "timestamp": time.time(),
        "participants": ["Alice", "Bob", "Charlie"],
        "content_type": "text",
        "raw_content": "This is a test message with important deadline information. Please review immediately.",
        "initial_salience": 0.75,
        "metadata": {"channel": "whatsapp", "context": "project_alpha"}
    }


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    return [
        "Regular team message",
        "Important meeting scheduled today",
        "Urgent deadline tomorrow",
        "Action required on task #123",
        "Decision needed for feature release",
        "Normal conversation text",
        "CONFIRM receipt of this message",
        "Task completed successfully",
        "Reminder: standup at 2pm",
        "Update the documentation"
    ]


@pytest.fixture
def large_text_document():
    """Generate a large text document for preprocessing tests."""
    base_text = "The quick brown fox jumps over the lazy dog. " * 100
    return base_text * 100  # ~45KB of text


@pytest.fixture
def mock_whatsapp_messages():
    """Mock WhatsApp message objects."""
    messages = []
    for i in range(50):
        msg = MagicMock()
        msg.body = f"Test message {i}"
        msg.timestamp = time.time() - (50 - i)
        msg.id._serialized = f"msg_{i:04d}"
        msg._data.notifyName = f"User_{i % 5}"
        msg.author = f"author_{i}"
        msg.from_ = f"from_{i}"
        messages.append(msg)
    return messages


@pytest.fixture
def mock_whatsapp_chat(mock_whatsapp_messages):
    """Mock WhatsApp chat object."""
    chat = MagicMock()
    chat.name = "Test Group Chat"
    chat.id._serialized = "chat_123_456"
    chat.isGroup = True
    chat.fetchMessages = MagicMock(return_value=mock_whatsapp_messages)
    return chat


@pytest.fixture(scope="session")
def pytest_configure():
    """Configure pytest with custom markers."""
    pytest.mark.performance = pytest.mark.performance
    pytest.mark.slow = pytest.mark.slow
    pytest.mark.integration = pytest.mark.integration


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
