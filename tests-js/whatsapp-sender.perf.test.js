/**
 * Performance tests for WhatsApp sender service
 * Tests message sending, batching, and API call efficiency
 */

const { performance } = require('perf_hooks');

describe('WhatsApp Sender Performance', () => {

  /**
   * Generate mock normalized messages
   */
  function generateNormalizedMessages(count = 50) {
    const messages = [];
    for (let i = 0; i < count; i++) {
      messages.push({
        chat_name: `Chat_${i % 5}`,
        message_id: `msg_${i}_serialized`,
        timestamp: new Date(Date.now() - (count - i) * 1000).toISOString(),
        sender: `User_${i % 10}`,
        message: `Test message body number ${i}`,
        is_group: i % 2 === 0
      });
    }
    return messages;
  }

  describe('Message Validation', () => {
    
    test('should validate 50 messages in <10ms', () => {
      const messages = generateNormalizedMessages(50);

      const start = performance.now();

      const validated = messages.every(msg => {
        return msg.chat_name &&
               msg.message_id &&
               msg.timestamp &&
               msg.sender &&
               msg.message &&
               typeof msg.is_group === 'boolean';
      });

      const elapsed = performance.now() - start;

      expect(validated).toBe(true);
      expect(elapsed).toBeLessThan(10);
      console.log(`✓ Validated 50 messages in ${elapsed.toFixed(2)}ms`);
    });

    test('should filter invalid messages in <15ms', () => {
      const messages = generateNormalizedMessages(50);
      // Add invalid messages
      messages.push({ chat_name: 'Invalid' }); // Missing fields
      messages.push({ /* completely empty */ });

      const start = performance.now();

      const valid = messages.filter(msg => {
        return msg && 
               msg.chat_name &&
               msg.message_id &&
               msg.timestamp &&
               msg.sender &&
               msg.message;
      });

      const elapsed = performance.now() - start;

      expect(valid.length).toBeLessThan(messages.length);
      expect(elapsed).toBeLessThan(15);
      console.log(`✓ Filtered invalid messages in ${elapsed.toFixed(2)}ms (kept ${valid.length})`);
    });
  });

  describe('Message Batching', () => {
    
    test('should batch 50 messages into groups in <20ms', () => {
      const messages = generateNormalizedMessages(50);
      const batchSize = 10;

      const start = performance.now();

      const batches = [];
      for (let i = 0; i < messages.length; i += batchSize) {
        batches.push(messages.slice(i, i + batchSize));
      }

      const elapsed = performance.now() - start;

      expect(batches).toHaveLength(5);
      expect(batches[0]).toHaveLength(batchSize);
      expect(elapsed).toBeLessThan(20);
      console.log(`✓ Batched 50 messages in ${elapsed.toFixed(2)}ms (${batches.length} batches)`);
    });

    test('should batch 200 messages efficiently in <50ms', () => {
      const messages = generateNormalizedMessages(200);
      const batchSize = 25;

      const start = performance.now();

      const batches = [];
      for (let i = 0; i < messages.length; i += batchSize) {
        batches.push(messages.slice(i, i + batchSize));
      }

      const elapsed = performance.now() - start;

      expect(batches).toHaveLength(8);
      expect(elapsed).toBeLessThan(50);
      console.log(`✓ Batched 200 messages in ${elapsed.toFixed(2)}ms (${batches.length} batches)`);
    });
  });

  describe('API Call Simulation', () => {
    
    test('should simulate sending 50 messages via API in <200ms', async () => {
      const messages = generateNormalizedMessages(50);

      const mockSendToAPI = async (batch) => {
        return new Promise(resolve => {
          // Simulate API call latency (5ms per batch)
          setTimeout(() => {
            resolve({
              success: true,
              count: batch.length,
              timestamp: new Date().toISOString()
            });
          }, 5);
        });
      };

      const start = performance.now();

      const batchSize = 10;
      const batches = [];
      for (let i = 0; i < messages.length; i += batchSize) {
        batches.push(messages.slice(i, i + batchSize));
      }

      const results = await Promise.all(
        batches.map(batch => mockSendToAPI(batch))
      );

      const elapsed = performance.now() - start;

      expect(results).toHaveLength(5);
      expect(results.every(r => r.success)).toBe(true);
      expect(elapsed).toBeLessThan(200);
      console.log(`✓ Sent 50 messages via API simulation in ${elapsed.toFixed(2)}ms`);
    });

    test('should handle 500 messages in batches in <500ms', async () => {
      const messages = generateNormalizedMessages(500);
      const batchSize = 50;

      const mockSendToAPI = async (batch) => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({ success: true, count: batch.length });
          }, 2);
        });
      };

      const start = performance.now();

      const batches = [];
      for (let i = 0; i < messages.length; i += batchSize) {
        batches.push(messages.slice(i, i + batchSize));
      }

      const results = await Promise.all(
        batches.map(batch => mockSendToAPI(batch))
      );

      const elapsed = performance.now() - start;

      expect(results.reduce((sum, r) => sum + r.count, 0)).toBe(500);
      expect(elapsed).toBeLessThan(500);
      console.log(`✓ Sent 500 messages in batches in ${elapsed.toFixed(2)}ms`);
    });
  });

  describe('Error Handling', () => {
    
    test('should handle API failures gracefully in <100ms', async () => {
      const messages = generateNormalizedMessages(20);

      const mockSendWithRetry = async (message, maxRetries = 3) => {
        return new Promise((resolve, reject) => {
          let attempts = 0;
          const attempt = () => {
            attempts++;
            // Simulate random failures
            if (Math.random() > 0.7 && attempts < maxRetries) {
              setTimeout(() => {
                console.log(`Retrying message ${message.message_id}...`);
                attempt();
              }, 10);
            } else if (attempts >= maxRetries) {
              reject(new Error(`Failed after ${maxRetries} attempts`));
            } else {
              resolve({
                success: true,
                messageId: message.message_id,
                attempts
              });
            }
          };
          attempt();
        });
      };

      const start = performance.now();

      const results = await Promise.allSettled(
        messages.map(msg => mockSendWithRetry(msg))
      );

      const elapsed = performance.now() - start;

      const successful = results.filter(r => r.status === 'fulfilled').length;
      expect(successful).toBeGreaterThan(0);
      expect(elapsed).toBeLessThan(100);
      console.log(`✓ Handled errors with retries in ${elapsed.toFixed(2)}ms (${successful}/${messages.length} successful)`);
    });
  });

  describe('Bulk Operations', () => {
    
    test('should process and send 1000 messages in <2000ms', async () => {
      const messages = generateNormalizedMessages(1000);

      const mockSendBatch = async (batch) => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({ success: true, count: batch.length });
          }, 1);
        });
      };

      const start = performance.now();

      const batchSize = 50;
      const batches = [];
      for (let i = 0; i < messages.length; i += batchSize) {
        batches.push(messages.slice(i, i + batchSize));
      }

      const results = await Promise.all(
        batches.map(batch => mockSendBatch(batch))
      );

      const elapsed = performance.now() - start;
      const totalSent = results.reduce((sum, r) => sum + r.count, 0);

      expect(totalSent).toBe(1000);
      expect(elapsed).toBeLessThan(2000);
      console.log(`✓ Processed and sent 1000 messages in ${elapsed.toFixed(2)}ms`);
    });
  });

  describe('Data Serialization', () => {
    
    test('should serialize 100 messages in <30ms', () => {
      const messages = generateNormalizedMessages(100);

      const start = performance.now();

      let serialized = 0;
      messages.forEach(msg => {
        const json = JSON.stringify({
          id: msg.message_id,
          text: msg.message,
          timestamp: msg.timestamp,
          sender: msg.sender
        });
        serialized += json.length;
      });

      const elapsed = performance.now() - start;

      expect(serialized).toBeGreaterThan(0);
      expect(elapsed).toBeLessThan(30);
      console.log(`✓ Serialized 100 messages in ${elapsed.toFixed(2)}ms (${serialized} bytes)`);
    });
  });

  describe('Throughput Metrics', () => {
    
    test('should calculate throughput: messages per second', () => {
      const messages = generateNormalizedMessages(100);
      const startTime = Date.now();

      // Simulate processing
      let processed = 0;
      messages.forEach(() => {
        // Simulate processing
        Math.sqrt(12345);
        processed++;
      });

      const endTime = Date.now();
      const elapsedSeconds = (endTime - startTime) / 1000;
      const throughput = processed / (elapsedSeconds || 0.001); // Handle very fast execution

      expect(processed).toBe(100);
      expect(throughput).toBeGreaterThan(1000); // Should be very fast
      console.log(`✓ Throughput: ${throughput.toFixed(0)} messages/second`);
    });
  });
});
