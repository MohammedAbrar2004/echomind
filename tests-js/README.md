# EchoMind JavaScript Tests

Performance tests for the WhatsApp service and related JavaScript modules.

## Quick Start

### Installation

```bash
npm install
```

### Running Tests

```bash
# All tests
npm test

# Performance tests only
npm run test:perf

# WhatsApp service tests
npm run test:whatsapp

# Sender service tests
npm run test:sender

# Watch mode (re-run on file change)
npm run test:watch
```

## Test Files

### whatsapp.perf.test.js
Tests for the WhatsApp client service (index.js)

**Coverage:**
- Message normalization (50, 200 messages)
- Empty message filtering
- Timestamp-based filtering
- Complete fetch cycles (1 chat, 5 chats)
- Date/timestamp operations
- Memory efficiency (1000 messages)

**Performance Targets:**
- Normalize 50 messages: **< 100ms**
- Normalize 200 messages: **< 300ms**
- 5-chat fetch cycle: **< 500ms**
- Process 1000 messages: **< 50MB memory**

### whatsapp-sender.perf.test.js
Tests for the WhatsApp sender service (sender.js)

**Coverage:**
- Message validation
- Batch grouping
- API call simulation
- Error handling and retries
- Bulk operations
- Message serialization
- Throughput metrics

**Performance Targets:**
- Validate 50 messages: **< 10ms**
- Batch 200 messages: **< 50ms**
- Send 500 via API: **< 500ms**
- Process 1000 messages: **< 2000ms**

## Test Structure

```
tests-js/
├── package.json
├── whatsapp.perf.test.js       # WhatsApp client tests
├── whatsapp-sender.perf.test.js # Sender service tests
└── README.md
```

## Running Individual Tests

### Run a single test file
```bash
npm test -- whatsapp.perf.test.js
```

### Run a single test suite
```bash
npm test -- --testNamePattern="Message Normalization"
```

### Run with debugging
```bash
node --inspect-brk node_modules/.bin/jest --runInBand whatsapp.perf.test.js
```

### Run with coverage
```bash
npm test -- --coverage
```

## Test Examples

### Basic Performance Test
```javascript
test('should complete in expected time', () => {
  const start = performance.now();
  
  // Code to test
  const result = normalizeMessages(messages);
  
  const elapsed = performance.now() - start;
  expect(elapsed).toBeLessThan(100); // < 100ms
  expect(result).toHaveLength(messages.length);
});
```

### Async Performance Test
```javascript
test('should fetch and process in acceptable time', async () => {
  const start = performance.now();
  
  const result = await chat.fetchMessages({ limit: 50 });
  
  const elapsed = performance.now() - start;
  expect(elapsed).toBeLessThan(200);
  expect(result).toBeDefined();
});
```

## Performance Monitoring

### Using performance.now()
```javascript
const start = performance.now();
// ... code to measure
const elapsed = performance.now() - start;
console.log(`Completed in ${elapsed.toFixed(2)}ms`);
```

### Memory Monitoring
```javascript
const before = process.memoryUsage().heapUsed;
// ... code to test
const after = process.memoryUsage().heapUsed;
const increase = (after - before) / 1024 / 1024; // MB
console.log(`Memory increase: ${increase.toFixed(2)}MB`);
```

## Troubleshooting

### Tests timeout
```bash
# Increase timeout (in milliseconds)
npm test -- --testTimeout=10000
```

### Memory issues
```javascript
// Monitor more carefully
test('memory test', () => {
  global.gc(); // Force garbage collection (run with --expose-gc)
  const start = process.memoryUsage().heapUsed;
  
  // Test code
  
  global.gc();
  const end = process.memoryUsage().heapUsed;
});

// Run with: node --expose-gc node_modules/.bin/jest
```

### Mock issues
Ensure mocks properly simulate the actual API:
```javascript
const mockChat = {
  fetchMessages: jest.fn().mockResolvedValue(mockMessages),
  // ... other properties
};
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run JavaScript Tests
  run: |
    cd tests-js
    npm install
    npm test
```

## Performance Expectations

| Operation | Target | File |
|-----------|--------|------|
| Normalize 50 msgs | < 100ms | whatsapp.perf.test.js |
| Normalize 200 msgs | < 300ms | whatsapp.perf.test.js |
| Fetch cycle (5 chats) | < 500ms | whatsapp.perf.test.js |
| Validate 50 msgs | < 10ms | whatsapp-sender.perf.test.js |
| Batch 200 msgs | < 50ms | whatsapp-sender.perf.test.js |
| Send 500 (API sim) | < 500ms | whatsapp-sender.perf.test.js |

## Adding New Tests

1. Create test in appropriate file (or new file)
2. Use `test()` or `it()` for individual tests
3. Use `describe()` for grouping
4. Include performance target in test name/docs
5. Add expectations for both functionality and timing

### Template
```javascript
describe('Feature Name', () => {
  test('should do something in acceptable time', () => {
    const start = performance.now();
    
    // Arrange
    const input = setupTestData();
    
    // Act
    const result = functionToTest(input);
    
    // Assert
    const elapsed = performance.now() - start;
    expect(elapsed).toBeLessThan(100);  // 100ms limit
    expect(result).toBeDefined();
    assert(result.isValid);
  });
});
```

## Performance Tips

1. **Cache computations** - Avoid repeated calculations
2. **Batch operations** - Group similar operations
3. **Async properly** - Use Promise.all() for parallel work
4. **Memory management** - Clean up large objects
5. **Profile first** - Use devtools/profiler before optimizing

## Debugging

### Console output
Add to tests to see logs:
```bash
npm test -- --verbose
```

### Inspect specific test
```javascript
test.only('inspect this one', () => {
  // Only this test runs
});
```

### Skip test temporarily
```javascript
test.skip('skip for now', () => {
  // This test is skipped
});
```

## Monitoring in Production

Track these metrics:
- Message fetch cycle duration
- Messages processed per cycle
- API response times
- Error rates and retry counts
- Memory heap size over time

---

For full test documentation, see [../tests.md](../tests.md)
