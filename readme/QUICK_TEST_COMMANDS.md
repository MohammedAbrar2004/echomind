# Quick Test Commands

Run these commands from the project root (`echomind/`)

## Python Tests

```bash
# Setup (first time only)
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run performance tests only
pytest tests/performance/ -v -m performance

# Run integration tests only
pytest tests/integration/ -v -m integration

# Run fast tests only (exclude slow)
pytest tests/ -v -m "not slow"

# Run specific test file
pytest tests/performance/test_db_performance.py -v

# Run specific test class
pytest tests/performance/test_db_performance.py::TestDatabasePerformance -v

# Run specific test method
pytest tests/performance/test_db_performance.py::TestDatabasePerformance::test_memory_chunk_insert_speed -v

# Run tests matching pattern
pytest tests/ -k "bulk" -v
pytest tests/ -k "normali" -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term
# View coverage: open htmlcov/index.html

# Run with verbose output (show print statements)
pytest tests/ -v -s

# Run tests in parallel (faster)
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Run failed tests first
pytest tests/ --ff
```

## JavaScript Tests

```bash
# Setup (first time only)
cd tests-js
npm install
cd ..

# Run all tests
npm --prefix tests-js test

# Run performance tests only  
npm --prefix tests-js run test:perf

# Run WhatsApp tests
npm --prefix tests-js run test:whatsapp

# Run sender tests
npm --prefix tests-js run test:sender

# Watch mode (re-run on changes)
npm --prefix tests-js run test:watch

# With coverage
npm --prefix tests-js test -- --coverage
```

## Combined (Both Python & JavaScript)

```bash
# Run all tests (Python + JavaScript)
pytest tests/ -v && npm --prefix tests-js test

# Run only performance tests
pytest tests/performance/ -v && npm --prefix tests-js run test:perf
```

## Test Selection by Module

```bash
# Database performance
pytest tests/performance/test_db_performance.py -v

# Preprocessing performance
pytest tests/performance/test_preprocessing_performance.py -v

# Pipeline performance
pytest tests/performance/test_pipeline_performance.py -v

# Connectors performance
pytest tests/performance/test_connectors_performance.py -v

# Scheduler performance
pytest tests/performance/test_scheduler_performance.py -v

# Integration tests
pytest tests/integration/ -v

# WhatsApp service (JavaScript)
npm --prefix tests-js run test:whatsapp

# Sender service (JavaScript)
npm --prefix tests-js run test:sender
```

## Test Selection by Performance Target

```bash
# Tests < 100ms
pytest tests/ -k "small or extract or creation or validation" -v

# Tests < 500ms
pytest tests/ -k "fetch or filter or insert or normali" -v

# Tests < 2 seconds
pytest tests/ -m "not slow" -v

# Slow tests (> 1 second)
pytest tests/ -m slow -v
```

## Development Workflow

```bash
# 1. Make code changes

# 2. Run specific test for your change
pytest tests/performance/test_preprocessing_performance.py::TestPreprocessorPerformance::test_clean_text_small -v -s

# 3. Run all tests in that module
pytest tests/performance/test_preprocessing_performance.py -v

# 4. Run all tests
pytest tests/ -v

# 5. Check coverage
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Debugging

```bash
# Show print statements
pytest tests/ -s

# Show variables on failure
pytest tests/ -l

# Show full diff on assertion failure
pytest tests/ -vv

# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger immediately
pytest tests/ --trace

# Run with full traceback
pytest tests/ --tb=long

# Run comparatively (before/after)
pytest tests/ --tb=no  # Minimal output
```

## Performance Profiling

```bash
# Time individual tests
pytest tests/performance/test_db_performance.py -v --durations=10
# Shows: 10 slowest tests

# Detailed timing
pytest tests/performance/test_db_performance.py -v --durations=0
# Shows: all test timings
```

## Output Filtering

```bash
# Show only tests that passed
pytest tests/ -v -q

# Show only tests that failed
pytest tests/ -v --tb=no | grep FAILED

# Quiet mode (less output)
pytest tests/ -q

# Very quiet (only summary)
pytest tests/ --quiet --quiet
```

## CI/CD Integration

```bash
# For GitHub Actions / CI pipelines
pytest tests/ --junit-xml=test-results.xml --cov=app --cov-report=xml

npm --prefix tests-js test -- --coverage --coverageReporters=cobertura
```

## Markers Reference

```bash
# Run tests with specific marker
pytest -m performance          # Performance tests
pytest -m integration          # Integration tests
pytest -m slow                 # Slow tests (>1s)
pytest -m unit                 # Unit tests

# Exclude tests with marker
pytest -m "not slow"           # All except slow
pytest -m "not integration"    # All except integration
```

## Tips & Tricks

```bash
# Quick sanity check
pytest tests/ -x --tb=short -q
# Stops on first failure, short output

# Performance regression check
pytest tests/performance/ -v --durations=5
# Shows 5 slowest tests - watch for regressions

# Full test with coverage and timing
pytest tests/ -v --cov=app --cov-report=html --durations=10

# Test specific functionality across modules
pytest -k "insert" -v
# Tests: insert_memory_chunk, bulk_insert, queue_insertion

# Test by data size
pytest -k "small or medium or large or bulk" -v

# Watch for flaky tests
pytest tests/ --count=10
# Runs each test 10 times to catch flakiness
```

## Common Scenarios

### "I changed the database module"
```bash
pytest tests/performance/test_db_performance.py -v
pytest tests/integration/test_pipeline_integration.py -v
```

### "I changed the preprocessor"
```bash
pytest tests/performance/test_preprocessing_performance.py -v
pytest tests/performance/test_pipeline_performance.py -v
```

### "I changed the WhatsApp service"
```bash
npm --prefix tests-js run test:whatsapp
pytest tests/performance/test_connectors_performance.py -v
```

### "Before committing code"
```bash
pytest tests/ -v --tb=short
npm --prefix tests-js test
```

### "Performance regression check"
```bash
pytest tests/ --durations=20 -v
# Check if any test is slower than expected
```

## Environment Variables

```bash
# Run tests without mocks (requires real connections)
TEST_WITH_REAL_DB=1 pytest tests/performance/test_db_performance.py -v

# Enable debug logging
PYTEST_DEBUG=1 pytest tests/ -v -s

# Disable performance checks
SKIP_PERFORMANCE_CHECKS=1 pytest tests/ -v
```

---

For more information, see:
- [tests/README.md](tests/README.md)
- [tests-js/README.md](tests-js/README.md)
- [tests.md](tests.md)
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
