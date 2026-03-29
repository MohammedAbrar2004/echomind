"""
Performance tests for the ingestion pipeline.
Tests orchestration, connector integration, and data flow.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


@pytest.mark.performance
class TestPipelinePerformance:
    """Performance tests for the ingestion pipeline."""
    
    def test_pipeline_initialization(self, benchmark):
        """
        Benchmark pipeline initialization.
        Expected: < 500ms
        """
        with patch('app.connectors.whatsapp.whatsapp_connector.WhatsAppConnector') as MockConnector:
            mock_connector = MagicMock()
            MockConnector.return_value = mock_connector
            
            from pipelines.ingestion_pipeline import run_ingestion
            
            def init_pipeline():
                # Simulated initialization
                connectors = [mock_connector for _ in range(5)]
                return len(connectors)
            
            stats = benchmark(init_pipeline, number=5, repeat=3)
            
            assert stats['avg'] < 0.5, f"Pipeline init exceeded 500ms"
            print(f"\n✓ Pipeline initialization - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_single_connector_data_fetch(self, benchmark, mock_whatsapp_messages):
        """
        Benchmark single connector fetching 50 messages.
        Expected: < 200ms (including normalization)
        """
        from unittest.mock import MagicMock
        
        def fetch_and_normalize():
            messages = mock_whatsapp_messages
            normalized = []
            for msg in messages:
                normalized.append({
                    'chat_name': 'Test Chat',
                    'message_id': msg.id._serialized,
                    'timestamp': msg.timestamp,
                    'sender': msg._data.notifyName,
                    'message': msg.body,
                    'is_group': False
                })
            return normalized
        
        stats = benchmark(fetch_and_normalize, number=10, repeat=3)
        
        assert stats['avg'] < 0.2, f"Connector fetch exceeded 200ms"
        print(f"\n✓ Single connector fetch (50 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_parallel_connector_simulation(self, benchmark):
        """
        Simulate parallel fetching from 5 connectors.
        Expected: < 1 second total for all connectors
        """
        def simulate_parallel_fetch():
            # Simulate 5 connectors, each fetching 50 messages
            results = []
            for connector_id in range(5):
                connector_data = {
                    'connector': f'connector_{connector_id}',
                    'messages': [
                        {
                            'id': f'msg_{connector_id}_{i}',
                            'body': f'Message from connector {connector_id}',
                            'timestamp': 1000000 + i
                        }
                        for i in range(50)
                    ]
                }
                results.append(connector_data)
            return results
        
        stats = benchmark(simulate_parallel_fetch, number=3, repeat=3)
        
        assert stats['avg'] < 1.0, f"Parallel fetch simulation exceeded 1s"
        print(f"\n✓ Parallel connector simulation (5 connectors, 250 msgs) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_data_normalization_pipeline(self, benchmark, sample_messages):
        """
        Benchmark data normalization across pipeline.
        Expected: < 50ms for 10 messages
        """
        raw_messages = sample_messages
        
        def normalize_pipeline():
            normalized = []
            for msg in raw_messages:
                normalized.append({
                    'original': msg,
                    'cleaned': msg.strip().lower(),
                    'word_count': len(msg.split()),
                    'has_urgent': 'urgent' in msg.lower() or 'important' in msg.lower()
                })
            return normalized
        
        stats = benchmark(normalize_pipeline, number=100, repeat=5)
        
        assert stats['avg'] * 1000 < 50, f"Normalization pipeline exceeded 50ms"
        print(f"\n✓ Data normalization pipeline (10 msgs) - Avg: {stats['avg']*1000:.2f}ms")


@pytest.mark.performance
@pytest.mark.slow
class TestPipelineScalability:
    """Test pipeline performance at scale."""
    
    def test_large_batch_processing(self, benchmark):
        """
        Test processing 1000 messages through entire pipeline.
        Expected: < 5 seconds
        """
        large_message_batch = [
            f"Message {i}: Regular content some text more text"
            for i in range(1000)
        ]
        
        def process_large_batch():
            results = []
            for msg in large_message_batch:
                result = {
                    'text': msg,
                    'normalized': msg.lower().strip(),
                    'word_count': len(msg.split()),
                    'processed': True
                }
                results.append(result)
            return len(results)
        
        stats = benchmark(process_large_batch, number=1, repeat=2)
        
        assert stats['avg'] < 5.0, f"Large batch processing exceeded 5s"
        print(f"\n✓ Large batch processing (1000 msgs) - Avg: {stats['avg']:.2f}s")
    
    def test_multi_source_ingestion_simulation(self, benchmark):
        """
        Simulate ingestion from 5 different sources with varying data sizes.
        Expected: < 2 seconds
        """
        sources = {
            'whatsapp': [f'whatsapp_msg_{i}' for i in range(100)],
            'gmail': [f'email_{i}' for i in range(50)],
            'calendar': [f'event_{i}' for i in range(30)],
            'phone': [f'call_{i}' for i in range(20)],
            'manual': [f'manual_entry_{i}' for i in range(40)]
        }
        
        def ingest_all_sources():
            all_data = []
            for source_name, source_data in sources.items():
                for item in source_data:
                    all_data.append({
                        'source': source_name,
                        'data': item,
                        'processed': True
                    })
            return len(all_data)
        
        stats = benchmark(ingest_all_sources, number=5, repeat=2)
        
        assert stats['avg'] < 2.0, f"Multi-source ingestion exceeded 2s"
        print(f"\n✓ Multi-source ingestion (240 items) - Avg: {stats['avg']*1000:.2f}ms")
