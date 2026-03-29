# EchoMind Test Documentation

## Overview

This document describes the comprehensive test suite for EchoMind, including performance benchmarks and integration tests for all modules.

## Directory Structure

```
echomind/
├── tests/                          # Python test suite
│   ├── conftest.py                # Shared pytest configuration and fixtures
│   ├── performance/               # Performance benchmark tests
│   │   ├── test_db_performance.py
│   │   ├── test_preprocessing_performance.py
│   │   ├── test_pipeline_performance.py
│   │   ├── test_connectors_performance.py
│   │   └── test_scheduler_performance.py
│   └── integration/               # Integration tests
│       └── test_pipeline_integration.py
├── tests-js/                      # JavaScript test suite
│   ├── package.json
│   ├── whatsapp.perf.test.js
│   └── whatsapp-sender.perf.test.js
└── tests.md                       # This file
```

## Python Tests

### Setup

1. **Install test dependencies:**
   ```bash
   pip install pytest pytest-cov
   ```

2. **Run all tests:**
   ```bash
   pytest tests/ -v
   ```

3. **Run only performance tests:**
   ```bash
   pytest tests/performance/ -v -m performance
   ```

4. **Run only integration tests:**
   ```bash
   pytest tests/integration/ -v -m integration
   ```

5. **Run specific test file:**
   ```bash
   pytest tests/performance/test_db_performance.py -v
   ```

6. **Run with coverage:**
   ```bash
   pytest tests/ --cov=app --cov-report=html
   ```

### Test Modules

#### 1. Database Performance Tests (`test_db_performance.py`)

**Purpose:** Benchmark database operations including insertion speed and bulk operations.

**Performance Targets:**
- Single memory chunk insertion: **< 100ms**
- Bulk insertion (100 chunks): **< 5 seconds**
- JSON serialization: **< 5ms**
- Cursor creation: **< 10ms**
- Large participant list (500): **< 50ms**

**Key Tests:**
- `test_memory_chunk_insert_speed` - Single insert performance
- `test_bulk_memory_chunk_insertion` - Batch insert performance
- `test_json_serialization_performance` - JSON encoding speed
- `test_large_participant_list_serialization` - Handles large data structures
- `test_large_metadata_object` - Complex nested object serialization

**Example Run:**
```bash
pytest tests/performance/test_db_performance.py::TestDatabasePerformance::test_memory_chunk_insert_speed -v
```

#### 2. Preprocessing Performance Tests (`test_preprocessing_performance.py`)

**Purpose:** Benchmark text cleaning, normalization, and salience scoring.

**Performance Targets:**
- Text cleaning (small): **< 1ms**
- Text cleaning (medium 45KB): **< 50ms**
- Participant normalization (5): **< 1ms**
- Participant normalization (500): **< 10ms**
- Salience scoring (10 messages): **< 5ms**
- Bulk salience scoring (1000): **< 500ms**

**Key Tests:**
- `test_clean_text_small` - Small text processing
- `test_clean_text_medium` - Medium-sized document processing
- `test_normalize_participants_small` - Small participant list
- `test_normalize_participants_large` - Large participant list
- `test_salience_scoring` - Individual message scoring
- `test_salience_scoring_bulk` - Bulk message scoring

#### 3. Pipeline Performance Tests (`test_pipeline_performance.py`)

**Purpose:** Benchmark end-to-end pipeline orchestration and data flow.

**Performance Targets:**
- Pipeline initialization: **< 500ms**
- Single connector fetch (50 msgs): **< 200ms**
- Parallel connector simulation (5 x 50 msgs): **< 1s**
- Data normalization (10 msgs): **< 50ms**
- Large batch (1000 msgs): **< 5s**
- Multi-source ingestion (240 items): **< 2s**

**Key Tests:**
- `test_pipeline_initialization` - Startup overhead
- `test_single_connector_data_fetch` - Individual connector performance
- `test_parallel_connector_simulation` - Multi-connector coordination
- `test_large_batch_processing` - Scalability testing
- `test_multi_source_ingestion_simulation` - Cross-source coordination

#### 4. Connectors Performance Tests (`test_connectors_performance.py`)

**Purpose:** Benchmark individual connector operations (fetch, normalize, filter).

**Performance Targets:**
- WhatsApp fetch & normalize (50): **< 100ms**
- Message filtering (50): **< 50ms**
- Sender extraction (50): **< 30ms**
- Timestamp conversion (50): **< 20ms**
- Large batch normalization (500): **< 500ms**

**Key Tests:**
- `test_whatsapp_message_fetch_and_normalize` - WhatsApp-specific operations
- `test_message_filtering_performance` - Filter empty/duplicate messages
- `test_sender_extraction_performance` - Extract sender information
- `test_timestamp_conversion_performance` - Convert timestamps to ISO format
- `test_large_message_batch_normalization` - Scale to 500 messages

#### 5. Scheduler Performance Tests (`test_scheduler_performance.py`)

**Purpose:** Benchmark task scheduling, interval checking, and execution.

**Performance Targets:**
- Task creation: **< 10ms**
- Task queue insertion (50): **< 50ms**
- Interval check (100 tasks): **< 5ms**
- Callback execution: **< 1ms**
- Large schedule check (500 tasks): **< 500ms**

**Key Tests:**
- `test_scheduler_task_creation` - Task object creation
- `test_task_queue_insertion` - Queue operations
- `test_interval_check_performance` - Due task detection
- `test_callback_execution_overhead` - Callback invocation timing
- `test_large_task_schedule` - Manage 500 concurrent tasks

### Pytest Markers

Use markers to filter test execution:

```bash
# Run only slow tests
pytest tests/ -m slow

# Run only performance tests
pytest tests/ -m performance

# Run integration tests
pytest tests/ -m integration

# Exclude slow tests
pytest tests/ -m "not slow"
```

## JavaScript Tests

### Setup

1. **Install dependencies:**
   ```bash
   cd tests-js
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

4. **Run WhatsApp tests:**
   ```bash
   npm run test:whatsapp
   ```

5. **Run sender tests:**
   ```bash
   npm run test:sender
   ```

6. **Watch mode:**
   ```bash
   npm run test:watch
   ```

### Test Files

#### 1. WhatsApp Service Tests (`whatsapp.perf.test.js`)

**Purpose:** Benchmark WhatsApp client operations and message processing.

**Performance Targets:**
- Normalize 50 messages: **< 100ms**
- Normalize 200 messages: **< 300ms**
- Filter 50 messages: **< 50ms**
- Filter by timestamp: **< 50ms**
- Single chat fetch cycle: **< 200ms**
- 5-chat fetch cycle (250 msgs): **< 500ms**
- Convert 100 timestamps: **< 20ms**
- Process 1000 messages: **< 50MB memory increase**

**Key Tests:**
- Message normalization performance
- Empty message filtering
- Timestamp-based filtering
- Complete fetch cycle simulation
- Multi-chat processing
- Memory efficiency

#### 2. Sender Service Tests (`whatsapp-sender.perf.test.js`)

**Purpose:** Benchmark message sending and API interaction.

**Performance Targets:**
- Validate 50 messages: **< 10ms**
- Filter invalid messages: **< 15ms**
- Batch 50 messages: **< 20ms**
- Batch 200 messages: **< 50ms**
- API send 50 messages: **< 200ms**
- API send 500 messages: **< 500ms**
- Handle 20 with retries: **< 100ms**
- Process 1000 messages: **< 2000ms**
- Serialize 100 messages: **< 30ms**

**Key Tests:**
- Message validation
- Batch grouping
- API call simulation
- Retry logic and error handling
- Bulk operations
- Serialization efficiency
- Throughput metrics

## Test Execution Examples

### Run All Tests with Summary
```bash
pytest tests/ -v --tb=short
```

### Run with Coverage Report
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run Specific Test Class
```bash
pytest tests/performance/test_db_performance.py::TestDatabasePerformance -v
```

### Run Tests Matching Pattern
```bash
pytest tests/ -k "bulk" -v
```

### Run JavaScript Tests with Output
```bash
cd tests-js && npm test -- --verbose
```

## Performance Expectations

### Python Modules

| Module | Operation | Target Time | Current |
|--------|-----------|------------|---------|
| Database | Single Insert | < 100ms | - |
| Database | Bulk Insert (100) | < 5s | - |
| Preprocessing | Clean Text (Small) | < 1ms | - |
| Preprocessing | Clean Text (Medium) | < 50ms | - |
| Preprocessing | Salience Score (1000) | < 500ms | - |
| Pipeline | Initialization | < 500ms | - |
| Pipeline | Multi-source (240 items) | < 2s | - |
| Connectors | Fetch & Normalize (50) | < 100ms | - |
| Scheduler | Large Schedule (500 tasks) | < 500ms | - |

### JavaScript Modules

| Module | Operation | Target Time | Current |
|--------|-----------|------------|---------|
| WhatsApp | Normalize (50) | < 100ms | - |
| WhatsApp | Normalize (200) | < 300ms | - |
| WhatsApp | Fetch Cycle (5 chats) | < 500ms | - |
| Sender | Validate (50) | < 10ms | - |
| Sender | Send Batch (500) | < 500ms | - |
| Sender | Process (1000) | < 2000ms | - |

## Fixtures

### Python Fixtures (conftest.py)

- **`benchmark`** - Custom benchmark function for timing operations
- **`mock_db_connection`** - Mock database connection and cursor
- **`sample_memory_chunk_data`** - Sample data for database tests
- **`sample_messages`** - Sample message list for preprocessing
- **`large_text_document`** - 45KB+ text for stress testing
- **`mock_whatsapp_messages`** - 50 mock WhatsApp message objects
- **`mock_whatsapp_chat`** - Mock WhatsApp chat object

### Usage Example

```python
def test_with_fixture(benchmark, sample_memory_chunk_data):
    """Test using provided fixtures."""
    with patch('app.db.repository.insert_memory_chunk'):
        stats = benchmark(
            insert_memory_chunk,
            mock_cursor,
            sample_memory_chunk_data,
            number=10,
            repeat=3
        )
    assert stats['avg'] < 0.1
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Python Tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --tb=short

- name: Run JavaScript Tests
  run: |
    cd tests-js
    npm install
    npm test
```

## Adding New Tests

### Python Tests

1. Create a new test file in `tests/performance/` or `tests/integration/`
2. Import pytest and fixtures from `conftest.py`
3. Use the `@pytest.mark.performance` or `@pytest.mark.integration` decorator
4. Write test functions starting with `test_`

```python
@pytest.mark.performance
def test_new_feature(benchmark, sample_data):
    """Test description."""
    stats = benchmark(function_to_test, sample_data, number=10, repeat=3)
    assert stats['avg'] < 0.1  # Expected time limit
```

### JavaScript Tests

1. Create a new test file named `*.perf.test.js` in `tests-js/`
2. Use Jest describe/test syntax
3. Use `performance.now()` for timing measurements

```javascript
describe('Feature Performance', () => {
  test('should complete in acceptable time', () => {
    const start = performance.now();
    // Test code
    const elapsed = performance.now() - start;
    expect(elapsed).toBeLessThan(100); // Time limit in ms
  });
});
```

## Troubleshooting

### Test Failures

`AssertionError: Average time exceeded limit`
- The tested code is slower than expected
- Check system load and available resources
- Consider increasing time limit if legitimate
- Optimize the code being tested

### Mock-Related Issues

Import errors in tests usually mean mocks need adjustment:
```python
from unittest.mock import patch, MagicMock
# Ensure patch paths match your imports
```

### JavaScript Test Issues

Missing modules:
```bash
npm install --save-dev jest benchmark
```

## Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use appropriate fixtures** - Leverage provided fixtures to avoid duplication
3. **Set realistic thresholds** - Base time limits on actual requirements
4. **Test at scale** - Include tests with realistic data volumes
5. **Monitor trends** - Track performance metrics over time
6. **Profile before optimizing** - Don't optimize without data
7. **Document assumptions** - Explain why a particular threshold exists

## Performance Tuning Tips

1. **Database queries** - Use EXPLAIN ANALYZE to identify bottlenecks
2. **Text processing** - Consider regex compilation caching
3. **Message filtering** - Optimize filter conditions for early exits
4. **Batch operations** - Identify optimal batch sizes
5. **Memory usage** - Monitor heap allocation in JavaScript
6. **API calls** - Use connection pooling and timeouts

---

**Last Updated:** March 30, 2026
**Test Count:** ~40 test cases
**Coverage:** Database, Preprocessing, Pipeline, Connectors, Scheduler, WhatsApp Service
