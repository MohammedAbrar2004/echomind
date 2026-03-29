"""
Performance tests for database operations.
Tests insertion speed, query performance, and bulk operations.
"""

import pytest
import time
import json
from unittest.mock import MagicMock, patch


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database repository module."""
    
    def test_memory_chunk_insert_speed(self, benchmark, sample_memory_chunk_data):
        """
        Benchmark single memory chunk insertion.
        Expected: < 100ms per insertion
        """
        with patch('app.db.repository.psycopg2') as mock_psycopg2:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ("uuid-123",)
            
            from app.db.repository import insert_memory_chunk
            
            stats = benchmark(
                insert_memory_chunk,
                mock_cursor,
                sample_memory_chunk_data,
                number=10,
                repeat=3
            )
            
            assert stats['avg'] < 0.1, f"Average insertion time {stats['avg']:.4f}s exceeds 100ms limit"
            print(f"\n✓ Single insert - Avg: {stats['avg']*1000:.2f}ms, Min: {stats['min']*1000:.2f}ms")
    
    def test_bulk_memory_chunk_insertion(self, benchmark, sample_memory_chunk_data):
        """
        Benchmark insertion of 100 memory chunks in batch.
        Expected: < 5 seconds for 100 chunks
        """
        test_data_list = [
            {**sample_memory_chunk_data, "external_message_id": f"msg_{i}"}
            for i in range(100)
        ]
        
        with patch('app.db.repository.psycopg2') as mock_psycopg2:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ("uuid-123",)
            
            from app.db.repository import insert_memory_chunk
            
            def insert_batch():
                for data in test_data_list:
                    insert_memory_chunk(mock_cursor, data)
            
            stats = benchmark(insert_batch, number=1, repeat=3)
            
            assert stats['avg'] < 5.0, f"Batch insertion time {stats['avg']:.2f}s exceeds 5s limit"
            print(f"\n✓ Bulk insert (100 chunks) - Avg: {stats['avg']:.2f}s, Min: {stats['min']:.2f}s")
    
    def test_json_serialization_performance(self, benchmark):
        """
        Benchmark JSON serialization of metadata and participants.
        Expected: < 5ms for typical data
        """
        complex_metadata = {
            "channel": "whatsapp",
            "context": "project_alpha",
            "tags": ["urgent", "meeting", "decision"],
            "nested": {
                "project_id": "proj_123",
                "taskid": "task_456",
                "details": {
                    "priority": "high",
                    "status": "active",
                    "participants_count": 5
                }
            },
            "history": [
                {"timestamp": time.time(), "action": "created"},
                {"timestamp": time.time(), "action": "updated"}
            ]
        }
        
        participants = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        
        def serialize_data():
            json.dumps(complex_metadata)
            json.dumps(participants)
        
        stats = benchmark(serialize_data, number=1000, repeat=3)
        
        assert stats['avg'] * 1000 < 5, f"JSON serialization {stats['avg']*1000:.2f}ms exceeds 5ms"
        print(f"\n✓ JSON serialization - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_cursor_creation_overhead(self, benchmark, mock_db_connection):
        """
        Benchmark cursor creation and connection overhead.
        Expected: < 10ms per cursor creation
        """
        mock_conn, _ = mock_db_connection
        
        def create_cursor():
            mock_conn.cursor()
        
        stats = benchmark(create_cursor, number=100, repeat=3)
        
        assert stats['avg'] * 1000 < 10, f"Cursor creation {stats['avg']*1000:.2f}ms exceeds 10ms"
        print(f"\n✓ Cursor creation - Avg: {stats['avg']*1000:.2f}ms")


@pytest.mark.performance
@pytest.mark.slow
class TestDatabaseScalability:
    """Test database performance under load."""
    
    def test_large_participant_list_serialization(self, benchmark):
        """
        Test serialization of large participant lists (100+ participants).
        Expected: < 50ms for 500 participants
        """
        large_participant_list = [f"User_{i}_Name_{i%100}" for i in range(500)]
        
        def serialize_large_list():
            json.dumps(large_participant_list)
        
        stats = benchmark(serialize_large_list, number=10, repeat=5)
        
        assert stats['avg'] * 1000 < 50, f"Large list serialization exceeds 50ms"
        print(f"\n✓ Large participant list (500) - Avg: {stats['avg']*1000:.2f}ms")
    
    def test_large_metadata_object(self, benchmark):
        """
        Test serialization of very large metadata objects.
        Expected: < 100ms for complex nested structures
        """
        large_metadata = {
            f"field_{i}": {
                "value": f"data_{i}",
                "nested_field": f"nested_{i}",
                "list_data": list(range(10))
            }
            for i in range(100)
        }
        
        def serialize_large_metadata():
            json.dumps(large_metadata)
        
        stats = benchmark(serialize_large_metadata, number=5, repeat=3)
        
        assert stats['avg'] * 1000 < 100, f"Large metadata serialization exceeds 100ms"
        print(f"\n✓ Large metadata object - Avg: {stats['avg']*1000:.2f}ms")
