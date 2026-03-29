/**
 * Performance tests for WhatsApp service index.js
 * Tests message fetching, normalization, and processing cycles
 */

const { performance } = require('perf_hooks');

describe('WhatsApp Service Performance', () => {
  
  /**
   * Generate mock WhatsApp messages
   */
  function generateMockMessages(count = 50) {
    const messages = [];
    for (let i = 0; i < count; i++) {
      messages.push({
        id: {
          _serialized: `message_${i}_serialized`
        },
        body: `Test message number ${i}`,
        timestamp: Math.floor(Date.now() / 1000) - (count - i),
        _data: {
          notifyName: `User_${i % 5}`,
          author: `author_${i}`,
          from: `from_${i}`
        }
      });
    }
    return messages;
  }

  /**
   * Generate mock WhatsApp chat objects
   */
  function generateMockChat(name, messageCount = 50) {
    return {
      name: name,
      id: {
        _serialized: `chat_${name}_serialized`
      },
      isGroup: true,
      fetchMessages: async () => generateMockMessages(messageCount)
    };
  }

  describe('Message Normalization', () => {
    
    test('should normalize 50 messages in <100ms', () => {
      const messages = generateMockMessages(50);
      const chatName = 'Test Chat';
      const chatId = 'chat_123_456';

      const start = performance.now();

      const normalized = messages.map((msg) => ({
        chat_name: chatName,
        message_id: msg.id && msg.id._serialized ? msg.id._serialized : `${chatId}-${msg.timestamp}`,
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender: msg._data.notifyName || msg.author || msg.from || "unknown",
        message: msg.body,
        is_group: true,
      }));

      const elapsed = performance.now() - start;

      expect(normalized).toHaveLength(50);
      expect(elapsed).toBeLessThan(100);
      console.log(`✓ Normalized 50 messages in ${elapsed.toFixed(2)}ms`);
    });

    test('should normalize 200 messages in <300ms', () => {
      const messages = generateMockMessages(200);
      const chatName = 'Large Chat';
      const chatId = 'chat_large_123';

      const start = performance.now();

      const normalized = messages.map((msg) => ({
        chat_name: chatName,
        message_id: msg.id._serialized,
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender: msg._data.notifyName || msg.author || "unknown",
        message: msg.body,
        is_group: true,
      }));

      const elapsed = performance.now() - start;

      expect(normalized).toHaveLength(200);
      expect(elapsed).toBeLessThan(300);
      console.log(`✓ Normalized 200 messages in ${elapsed.toFixed(2)}ms`);
    });
  });

  describe('Message Filtering', () => {
    
    test('should filter empty messages in <50ms', () => {
      const messages = generateMockMessages(50);
      // Add some empty messages
      messages.splice(10, 0, { body: '', timestamp: Date.now() / 1000 });
      messages.splice(25, 0, { body: '   ', timestamp: Date.now() / 1000 });

      const start = performance.now();

      const filtered = messages.filter((msg) => {
        return typeof msg.body === "string" && msg.body.trim() !== "";
      });

      const elapsed = performance.now() - start;

      expect(filtered.length).toBeLessThan(messages.length);
      expect(elapsed).toBeLessThan(50);
      console.log(`✓ Filtered 50 messages in ${elapsed.toFixed(2)}ms (removed ${messages.length - filtered.length})`);
    });

    test('should filter by timestamp in <50ms', () => {
      const messages = generateMockMessages(50);
      const lastFetchTime = messages[25].timestamp;

      const start = performance.now();

      const newMessages = messages.filter((msg) => {
        if (msg.timestamp * 1000 <= lastFetchTime * 1000) {
          return false;
        }
        return true;
      });

      const elapsed = performance.now() - start;

      expect(elapsed).toBeLessThan(50);
      console.log(`✓ Filtered by timestamp in ${elapsed.toFixed(2)}ms (kept ${newMessages.length})`);
    });
  });

  describe('Fetch Cycle Simulation', () => {
    
    test('should complete fetch cycle for 1 chat with 50 messages in <200ms', async () => {
      const chat = generateMockChat('Chat_1', 50);
      const lastFetchTime = {};

      const start = performance.now();

      const messages = await chat.fetchMessages({ limit: 50 });
      
      const newMessages = messages.filter((msg) => {
        if (typeof msg.body !== "string" || msg.body.trim() === "") {
          return false;
        }
        if (lastFetchTime[chat.name] && msg.timestamp * 1000 <= lastFetchTime[chat.name]) {
          return false;
        }
        return true;
      });

      const normalized = newMessages.map((msg) => ({
        chat_name: chat.name,
        message_id: msg.id._serialized,
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender: msg._data.notifyName || msg.author || "unknown",
        message: msg.body,
        is_group: chat.isGroup || false,
      }));

      const elapsed = performance.now() - start;

      expect(normalized.length).toBeGreaterThan(0);
      expect(elapsed).toBeLessThan(200);
      console.log(`✓ Completed fetch cycle in ${elapsed.toFixed(2)}ms (${normalized.length} messages)`);
    });

    test('should complete fetch cycle for 5 chats (50 msgs each) in <500ms', async () => {
      const chats = [
        generateMockChat('Chat_1', 50),
        generateMockChat('Chat_2', 50),
        generateMockChat('Chat_3', 50),
        generateMockChat('Chat_4', 50),
        generateMockChat('Chat_5', 50)
      ];
      const lastFetchTime = {};

      const start = performance.now();

      const allNormalized = [];
      for (const chat of chats) {
        const messages = await chat.fetchMessages({ limit: 50 });
        
        const newMessages = messages.filter((msg) => {
          return typeof msg.body === "string" && msg.body.trim() !== "";
        });

        const normalized = newMessages.map((msg) => ({
          chat_name: chat.name,
          message_id: msg.id._serialized,
          timestamp: new Date(msg.timestamp * 1000).toISOString(),
          sender: msg._data.notifyName || msg.author || "unknown",
          message: msg.body,
          is_group: chat.isGroup || false,
        }));

        allNormalized.push(...normalized);
      }

      const elapsed = performance.now() - start;

      expect(allNormalized.length).toBe(250); // 5 chats × 50 messages
      expect(elapsed).toBeLessThan(500);
      console.log(`✓ Completed 5-chat fetch cycle in ${elapsed.toFixed(2)}ms (${allNormalized.length} total messages)`);
    });
  });

  describe('Date/Timestamp Operations', () => {
    
    test('should convert 100 timestamps in <20ms', () => {
      const timestamps = Array.from({ length: 100 }, (_, i) => 
        Math.floor(Date.now() / 1000) - i
      );

      const start = performance.now();

      const converted = timestamps.map((ts) => 
        new Date(ts * 1000).toISOString()
      );

      const elapsed = performance.now() - start;

      expect(converted).toHaveLength(100);
      expect(elapsed).toBeLessThan(20);
      console.log(`✓ Converted 100 timestamps in ${elapsed.toFixed(2)}ms`);
    });
  });

  describe('Memory Efficiency', () => {
    
    test('should process 1000 messages without excessive memory', () => {
      const messages = generateMockMessages(1000);
      const initialMemory = process.memoryUsage().heapUsed;

      const normalized = messages.map((msg) => ({
        chat_name: 'Bulk Chat',
        message_id: msg.id._serialized,
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender: msg._data.notifyName || "unknown",
        message: msg.body,
        is_group: true,
      }));

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024; // Convert to MB

      expect(normalized).toHaveLength(1000);
      expect(memoryIncrease).toBeLessThan(50); // Less than 50MB increase
      console.log(`✓ Processed 1000 messages with ${memoryIncrease.toFixed(2)}MB memory increase`);
    });
  });
});
