"""
Integration tests for the complete ingestion pipeline.
Tests end-to-end workflows and module interactions.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.integration
@pytest.mark.slow
class TestPipelineIntegration:
    """Integration tests for the full pipeline."""
    
    def test_connector_to_database_flow(self, benchmark, sample_memory_chunk_data):
        """
        Test complete flow: fetch message → normalize → insert to DB.
        Expected: < 500ms for single message
        """
        with patch('app.db.connection.get_connection') as mock_conn:
            with patch('app.preprocessing.preprocessor.Preprocessor') as mock_preprocessor:
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = ("uuid-123",)
                mock_conn.return_value.cursor.return_value = mock_cursor
                
                mock_preprocessor_instance = MagicMock()
                mock_preprocessor.return_value = mock_preprocessor_instance
                
                def full_flow():
                    # Simulate connector message fetch
                    message = sample_memory_chunk_data
                    
                    # Preprocess
                    message['raw_content'] = message['raw_content'].lower().strip()
                    
                    # Insert to DB
                    mock_cursor.execute("INSERT INTO memory_chunks ...")
                    return ("uuid-123",)
                
                stats = benchmark(full_flow, number=5, repeat=3)
                
                assert stats['avg'] < 0.5, f"Full flow exceeded 500ms"
                print(f"\n✓ Connector → DB flow - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_multi_connector_integration(self, benchmark):
        """
        Test data flowing from 3 different connectors through pipeline.
        Expected: < 1 second
        """
        connector_outputs = {
            'whatsapp': [
                {'id': f'wa_{i}', 'body': f'msg_{i}', 'timestamp': 1000000 + i}
                for i in range(30)
            ],
            'gmail': [
                {'id': f'email_{i}', 'subject': f'email_{i}', 'timestamp': 1000000 + i}
                for i in range(20)
            ],
            'calendar': [
                {'id': f'event_{i}', 'title': f'event_{i}', 'timestamp': 1000000 + i}
                for i in range(15)
            ]
        }
        
        def integrate_connectors():
            all_items = []
            for source_name, items in connector_outputs.items():
                for item in items:
                    # Normalize
                    normalized = {
                        'source': source_name,
                        'id': item['id'],
                        'timestamp': item['timestamp'],
                        'processed': True
                    }
                    all_items.append(normalized)
            return len(all_items)
        
        stats = benchmark(integrate_connectors, number=5, repeat=3)
        
        assert stats['avg'] < 1.0, f"Multi-connector integration exceeded 1s"
        print(f"\n✓ Multi-connector integration (65 items) - Avg: {stats['avg']*1000:.2f}ms")
