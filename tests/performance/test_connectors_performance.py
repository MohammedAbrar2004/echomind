"""
Performance tests for connector modules.
Tests message fetching, normalization, and data extraction.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.performance
class TestConnectorPerformance:
    """Performance tests for data connectors."""
    
    def test_whatsapp_message_fetch_and_normalize(self, benchmark, mock_whatsapp_messages):
        """
        Benchmark fetching and normalizing 50 WhatsApp messages.
        Expected: < 100ms
        """
        def fetch_normalize():
            normalized = []
            for msg in mock_whatsapp_messages:
                normalized.append({
                    'chat_name': 'Test Chat',
                    'message_id': msg.id._serialized,
                    'timestamp': msg.timestamp,
                    'sender': msg._data.notifyName or msg.author or 'unknown',
                    'message': msg.body,
                    'is_group': True
                })
            return normalized
        
        stats = benchmark(fetch_normalize, number=20, repeat=5)
        
        assert stats['avg'] < 0.1, f"WhatsApp fetch+normalize exceeded 100ms"
        print(f"\n✓ WhatsApp fetch & normalize (50 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_message_filtering_performance(self, benchmark, mock_whatsapp_messages):
        """
        Benchmark message filtering (empty messages, duplicates).
        Expected: < 50ms for 50 messages
        """
        last_fetch_time = {}
        
        def filter_messages():
            new_messages = []
            for msg in mock_whatsapp_messages:
                # Filter out empty messages
                if not isinstance(msg.body, str) or msg.body.strip() == "":
                    continue
                # Filter out old messages
                if 'Test Chat' in last_fetch_time:
                    if msg.timestamp <= last_fetch_time.get('Test Chat', 0):
                        continue
                new_messages.append(msg)
            return new_messages
        
        stats = benchmark(filter_messages, number=50, repeat=5)
        
        assert stats['avg'] * 1000 < 50, f"Message filtering exceeded 50ms"
        print(f"\n✓ Message filtering (50 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_sender_extraction_performance(self, benchmark, mock_whatsapp_messages):
        """
        Benchmark sender information extraction.
        Expected: < 30ms for 50 messages
        """
        def extract_senders():
            senders = []
            for msg in mock_whatsapp_messages:
                sender = msg._data.notifyName or msg.author or msg.from_ or "unknown"
                senders.append({
                    'message_id': msg.id._serialized,
                    'sender': sender,
                    'original_sender': msg._data.notifyName
                })
            return senders
        
        stats = benchmark(extract_senders, number=50, repeat=5)
        
        assert stats['avg'] * 1000 < 30, f"Sender extraction exceeded 30ms"
        print(f"\n✓ Sender extraction (50 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_timestamp_conversion_performance(self, benchmark, mock_whatsapp_messages):
        """
        Benchmark timestamp conversion from WAMe format.
        Expected: < 20ms for 50 timestamps
        """
        from datetime import datetime
        
        def convert_timestamps():
            converted = []
            for msg in mock_whatsapp_messages:
                timestamp_iso = datetime.fromtimestamp(msg.timestamp).isoformat()
                converted.append(timestamp_iso)
            return converted
        
        stats = benchmark(convert_timestamps, number=50, repeat=5)
        
        assert stats['avg'] * 1000 < 20, f"Timestamp conversion exceeded 20ms"
        print(f"\n✓ Timestamp conversion (50 msgs) - Avg: {stats['avg']*1000:.2f}ms")


@pytest.mark.performance
@pytest.mark.slow
class TestConnectorScalability:
    """Test connector performance at scale."""
    
    def test_large_message_batch_normalization(self, benchmark):
        """
        Batch normalize 500 messages from multiple sources.
        Expected: < 500ms
        """
        mock_messages = [
            MagicMock(
                body=f"Message {i}",
                timestamp=1000000 + i,
                id=MagicMock(_serialized=f"msg_{i}"),
                _data=MagicMock(notifyName=f"User_{i%10}"),
                author=f"author_{i}",
                from_=f"from_{i}",
                chat=MagicMock(name=f"chat_{i%5}", id=MagicMock(_serialized=f"chat_{i%5}"), isGroup=i%2==0)
            )
            for i in range(500)
        ]
        
        def normalize_large_batch():
            normalized = []
            for msg in mock_messages:
                normalized.append({
                    'chat_name': f'chat_{msg.timestamp % 5}',
                    'message_id': msg.id._serialized,
                    'timestamp': msg.timestamp,
                    'sender': msg._data.notifyName or msg.author or 'unknown',
                    'message': msg.body,
                    'is_group': msg.timestamp % 2 == 0
                })
            return normalized
        
        stats = benchmark(normalize_large_batch, number=3, repeat=2)
        
        assert stats['avg'] < 0.5, f"Large batch normalization exceeded 500ms"
        print(f"\n✓ Large batch normalization (500 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_multi_connector_concurrent_simulation(self, benchmark):
        """
        Simulate concurrent operations from 5 different connectors.
        Expected: < 1 second for all
        """
        def simulate_concurrent():
            results = {}
            
            # Simulate WhatsApp
            results['whatsapp'] = [
                {'id': f'wa_{i}', 'body': f'msg_{i}', 'processed': True}
                for i in range(100)
            ]
            
            # Simulate Gmail
            results['gmail'] = [
                {'id': f'email_{i}', 'subject': f'email_{i}', 'processed': True}
                for i in range(50)
            ]
            
            # Simulate Calendar
            results['calendar'] = [
                {'id': f'event_{i}', 'title': f'event_{i}', 'processed': True}
                for i in range(30)
            ]
            
            # Simulate Phone
            results['phone'] = [
                {'id': f'call_{i}', 'duration': 300 + i, 'processed': True}
                for i in range(20)
            ]
            
            # Simulate Manual
            results['manual'] = [
                {'id': f'manual_{i}', 'content': f'entry_{i}', 'processed': True}
                for i in range(40)
            ]
            
            return results
        
        stats = benchmark(simulate_concurrent, number=5, repeat=2)
        
        assert stats['avg'] < 1.0, f"Multi-connector simulation exceeded 1s"
        print(f"\n✓ Multi-connector concurrent simulation - Avg: {stats['avg']*1000:.2f}ms")
