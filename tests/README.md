# EchoMind Test Suite

This directory contains comprehensive performance and integration tests for all EchoMind modules.

## Quick Start

### Python Tests

1. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Run all tests:**
   ```bash
   pytest
   ```

3. **Run performance tests only:**
   ```bash
   pytest -m performance
   ```

4. **Run with coverage:**
   ```bash
   pytest --cov=app --cov-report=html
   ```

### JavaScript Tests

1. **Install dependencies:**
   ```bash
   cd ../tests-js
   npm install
   ```

2. **Run all tests:**
   ```bash
   npm test
   ```

3. **Run performance tests:**
   ```bash
   npm run test:perf
   ```

## Test Structure

- **`conftest.py`** - Shared fixtures and pytest configuration
- **`performance/`** - Performance benchmarks for all modules
  - `test_db_performance.py` - Database operations
  - `test_preprocessing_performance.py` - Text processing
  - `test_pipeline_performance.py` - End-to-end pipeline
  - `test_connectors_performance.py` - Data connector operations
  - `test_scheduler_performance.py` - Task scheduling
- **`integration/`** - Integration tests
  - `test_pipeline_integration.py` - Cross-module interactions

## Performance Targets

| Operation | Target | Module |
|-----------|--------|--------|
| Single DB insert | < 100ms | Database |
| Text cleaning (45KB) | < 50ms | Preprocessing |
| Message normalization (50) | < 100ms | Pipeline |
| Salience scoring (1000) | < 500ms | Preprocessing |
| Multi-source ingestion (240) | < 2s | Pipeline |
| WhatsApp fetch (5 chats) | < 500ms | Service |

## Running Tests

### By Category
```bash
pytest -m performance      # Performance only
pytest -m integration      # Integration only
pytest -m slow            # Slow tests (>1s)
pytest -m "not slow"      # Fast tests only
```

### By Module
```bash
pytest performance/test_db_performance.py
pytest performance/test_preprocessing_performance.py
pytest integration/test_pipeline_integration.py
```

### By Test Name
```bash
pytest -k "bulk"          # Tests with "bulk" in name
pytest -k "normalize"     # Tests with "normalize" in name
```

### With Verbose Output
```bash
pytest -v --tb=short      # Verbose with short traceback
pytest -vv                # Very verbose
```

## Fixtures

Available fixtures in `conftest.py`:

- `benchmark` - Function timing and statistics
- `mock_db_connection` - Mock database cursor
- `sample_memory_chunk_data` - Test data for DB operations
- `sample_messages` - Sample message list
- `large_text_document` - 45KB+ test document
- `mock_whatsapp_messages` - Mock WhatsApp message objects
- `mock_whatsapp_chat` - Mock chat with messages

## Example Test Run

```bash
# Run performance tests with coverage
pytest performance/ -v --cov=app --cov-report=term

# Output:
# performance/test_db_performance.py::TestDatabasePerformance::test_memory_chunk_insert_speed PASSED
# ✓ Single insert - Avg: 45.23ms, Min: 42.10ms
#
# performance/test_preprocessing_performance.py::TestPreprocessorPerformance::test_clean_text_medium PASSED
# ✓ Clean text (medium 45KB) - Avg: 38.45ms, Min: 35.12ms
```

## CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Run Tests
  run: |
    cd echomind
    pip install -r requirements.txt
    pytest tests/ -v --cov=app
```

## Performance Thresholds

If a test fails due to timing:

1. Check system load (`top`, Task Manager)
2. Verify local environment hasn't changed
3. Update threshold if legitimate (add comment explaining why)
4. Profile code for optimization opportunities

Example threshold adjustment:
```python
def test_something(benchmark, fixture):
    stats = benchmark(func, number=10, repeat=3)
    
    # Old: assert stats['avg'] < 0.1
    # Increased from 100ms to 150ms based on profiling
    assert stats['avg'] < 0.15  # ← Updated threshold
```

## Contributing Tests

When adding new tests:

1. Place performance tests in `performance/`
2. Place integration tests in `integration/`
3. Use appropriate markers (`@pytest.mark.performance`, etc.)
4. Include performance targets in docstrings
5. Use fixtures from `conftest.py` when possible
6. Write clear assertions with meaningful messages

Example:
```python
@pytest.mark.performance
def test_my_feature(benchmark, fixture_name):
    """Test description.
    
    Expected: < 100ms for 50 items
    """
    stats = benchmark(function, fixture_name, number=10, repeat=3)
    
    assert stats['avg'] < 0.1, f"Avg {stats['avg']:.3f}s exceeds 100ms limit"
    print(f"\n✓ Feature test - Avg: {stats['avg']*1000:.2f}ms")
```

## Troubleshooting

**Tests are flaky (sometimes pass, sometimes fail):**
- Check system resources during test execution
- Increase timing thresholds if appropriate
- Profile code to find actual bottlenecks

**ImportError when running tests:**
```bash
# Ensure you're running from project root
pwd  # Should show .../echomind
pytest tests/
```

**Mock not working:**
```python
# Ensure patch path matches import
from app.module import function
# Patch where it's used, not where it's defined
with patch('app.module.function'):
    ...
```

---

For full documentation, see [tests.md](../tests.md)
