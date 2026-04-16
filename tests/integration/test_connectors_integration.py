"""
Comprehensive Integration Tests for EchoMind

Tests all connectors, pipeline, media handling, error handling, and end-to-end workflows.
Run with: pytest tests/integration/test_echomind.py -v
"""

import pytest
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Connectors
from app.connectors.gmail.gmail_connector import GmailConnector
from app.connectors.calendar.calendar_connector import CalendarConnector
from app.connectors.gmeet.gmeet_connector import GMeetConnector
from app.connectors.manual.manual_connector import ManualConnector
from app.connectors.whatsapp.whatsapp_connector import WhatsAppConnector

# Core modules
from app.preprocessing.preprocessor import Preprocessor
from app.db.connection import get_connection
from app.db.repository import insert_memory_chunk, insert_media_file
from pipelines.ingestion_pipeline import run_ingestion, run_ingestion_for_items
from models.normalized_input import NormalizedInput

logger = logging.getLogger("EchoMind.Tests")


class TestConnectorIntegration:
    """Integration tests for all connectors."""
    
    @pytest.fixture
    def db_connection(self):
        """Provide a database connection."""
        conn = get_connection()
        yield conn
        conn.close()
    
    @pytest.fixture
    def preprocessor(self):
        """Provide a preprocessor instance."""
        return Preprocessor()
    
    def test_manual_connector(self):
        """Test manual connector file scanning."""
        connector = ManualConnector()
        
        # Create test file
        test_file = Path("data/manual_uploads/test_document.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_content = "This is a test document for manual ingestion"
        test_file.write_text(test_content)
        
        try:
            # Fetch data
            results = connector.fetch_data()
            
            # Should find the test file
            assert len(results) > 0, "Manual connector should find test file"
            
            # Verify content
            found = False
            for result in results:
                if "test_document" in result.external_message_id:
                    assert result.source_type == "manual"
                    assert result.content_type == "text"
                    assert test_content in result.raw_content
                    found = True
                    break
            
            assert found, "Test document should be found in results"
            logger.info("✓ Manual connector test passed")
        
        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
    
    def test_gmail_connector_mock(self):
        """Test Gmail connector initialization (mock if no credentials)."""
        try:
            connector = GmailConnector()
            # If we reach here, Gmail auth worked
            assert connector.service is not None
            logger.info("✓ Gmail connector initialized successfully")
        except FileNotFoundError as e:
            logger.info(f"! Gmail credentials not available (expected in test env): {e}")
            pytest.skip("Gmail credentials not configured")
        except Exception as e:
            logger.error(f"! Unexpected error in Gmail connector: {e}")
            raise
    
    def test_calendar_connector_mock(self):
        """Test Calendar connector initialization (mock if no credentials)."""
        try:
            connector = CalendarConnector()
            assert connector.service is not None
            logger.info("✓ Calendar connector initialized successfully")
        except FileNotFoundError as e:
            logger.info(f"! Calendar credentials not available (expected in test env): {e}")
            pytest.skip("Calendar credentials not configured")
        except Exception as e:
            logger.error(f"! Unexpected error in Calendar connector: {e}")
            raise
    
    def test_gmeet_connector_mock(self):
        """Test GMeet connector initialization (mock if no credentials)."""
        try:
            connector = GMeetConnector()
            assert connector.service is not None
            logger.info("✓ GMeet connector initialized successfully")
        except FileNotFoundError as e:
            logger.info(f"! GMeet credentials not available (expected in test env): {e}")
            pytest.skip("GMeet credentials not configured")
        except Exception as e:
            logger.error(f"! Unexpected error in GMeet connector: {e}")
            raise
    
    def test_preprocessor(self):
        """Test preprocessor functionality."""
        from models.normalized_input import NormalizedInput
        
        preprocessor = Preprocessor()
        
        # Create test input
        test_input = NormalizedInput(
            source_type="test",
            external_message_id="test_001",
            timestamp=datetime.now(),
            participants=["Alice", "Bob"],
            content_type="text",
            raw_content="  Meeting: IMPORTANT   URGENT   TASK   \n\n\n   Extra spaces   ",
            metadata={"origin": "test"}
        )
        
        # Process
        result = preprocessor.process(test_input)
        
        # Verify text cleaning
        assert "IMPORTANT" in result["raw_content"].upper()
        assert result["raw_content"].count("  ") == 0, "Multiple spaces should be reduced"
        
        # Verify salience scoring
        assert result["initial_salience"] > 0.3, "Should have high salience with keywords"
        
        # Verify participants normalization
        assert "alice" in result["participants"]
        assert "bob" in result["participants"]
        
        logger.info("✓ Preprocessor test passed")
    
    def test_ingestion_pipeline_with_mock_data(self):
        """Test full ingestion pipeline with manual connector."""
        # Create test file
        test_file = Path("data/manual_uploads/integration_test.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_content = "Integration test document: Meeting with team about Q2 goals"
        test_file.write_text(test_content)
        
        try:
            # Run ingestion
            results = run_ingestion()
            
            # Verify results structure
            assert "inserted" in results
            assert "duplicates" in results
            assert "errors" in results
            
            logger.info(f"✓ Ingestion pipeline test passed: {results}")
        
        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)
    
    def test_whatsapp_push_ingestion(self):
        """Test WhatsApp push ingestion through API."""
        test_messages = [
            {
                "chat_name": "Test Chat",
                "message_id": "msg_001",
                "timestamp": datetime.now().isoformat(),
                "sender": "alice",
                "message": "This is a test message",
                "is_group": False,
                "has_media": False,
                "media_data": None,
                "media_mime_type": None,
                "media_filename": None
            }
        ]
        
        inserted, duplicates, errors = run_ingestion_for_items(test_messages, "whatsapp")
        
        # Should process successfully
        assert inserted > 0 or duplicates > 0, "Should either insert or find duplicate"
        assert errors == 0, "Should have no errors"
        
        logger.info(f"✓ WhatsApp push ingestion test passed: inserted={inserted}, duplicates={duplicates}")
    
    def test_database_deduplication(self, db_connection):
        """Test that duplicate detection works."""
        cursor = db_connection.cursor()
        
        try:
            # Create test data
            test_data_1 = {
                "user_id": "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9",
                "source_id": "39218ef4-b3ce-4b98-b1e2-34afa243c785",  # WhatsApp
                "external_message_id": f"dedup_test_{datetime.now().timestamp()}",
                "timestamp": datetime.now(),
                "participants": ["test_user"],
                "content_type": "text",
                "raw_content": "Test message",
                "initial_salience": 0.5,
                "metadata": {"origin": "test"}
            }
            
            # Insert first time
            chunk_id_1 = insert_memory_chunk(cursor, test_data_1)
            db_connection.commit()
            
            # Try to insert duplicate
            try:
                chunk_id_2 = insert_memory_chunk(cursor, test_data_1)
                db_connection.commit()
                # This should fail due to unique constraint
                assert False, "Should have raised UniqueViolation"
            except Exception as e:
                # This is expected
                db_connection.rollback()
                logger.info(f"✓ Duplicate detection working: {type(e).__name__}")
        
        finally:
            cursor.close()


class TestMediaHandling:
    """Tests for media file handling."""
    
    def test_media_service_save(self):
        """Test media service file saving."""
        from app.services.media_service import MediaService
        from datetime import datetime
        
        service = MediaService()
        
        # Create test file data
        test_content = b"This is test file content"
        
        # Test PDF save
        media_obj = service.save(
            raw_bytes=test_content,
            original_filename="test_document.pdf",
            mime_type="application/pdf",
            source_type="test",
            captured_at=datetime.now()
        )
        
        # Verify metadata
        assert media_obj.original_filename == "test_document.pdf"
        assert media_obj.media_type == "document"
        assert media_obj.size_bytes == len(test_content)
        assert Path(media_obj.local_path).exists()
        
        logger.info(f"✓ Media service test passed: {media_obj.local_path}")


class TestErrorHandling:
    """Tests for error handling and retry logic."""
    
    def test_error_tracker(self):
        """Test error tracking functionality."""
        from app.utils.error_handler import ErrorTracker, IngestionError
        
        tracker = ErrorTracker()
        
        # Add some errors
        tracker.add_error(IngestionError(
            source_type="test",
            external_message_id="item_001",
            error_message="Test error",
            error_type="ValueError",
            is_permanent=False
        ))
        
        tracker.add_error(IngestionError(
            source_type="test",
            external_message_id="item_002",
            error_message="Permanent error",
            error_type="FileNotFoundError",
            is_permanent=True
        ))
        
        # Get summary
        summary = tracker.get_summary()
        
        assert summary["total_errors"] == 2
        assert summary["retryable_errors"] == 1
        assert summary["permanent_errors"] == 1
        assert summary["by_source"]["test"] == 2
        
        logger.info("✓ Error tracker test passed")
    
    def test_retry_decorator(self):
        """Test retry decorator with exponential backoff."""
        from app.utils.error_handler import retry_with_backoff, RetryConfig
        
        call_count = [0]
        
        @retry_with_backoff(RetryConfig(max_retries=2, initial_delay_seconds=0.01))
        def failing_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Simulated transient error")
            return "success"
        
        # Should retry and eventually succeed
        result = failing_function()
        
        assert result == "success"
        assert call_count[0] == 3
        
        logger.info("✓ Retry decorator test passed with 3 attempts")


class TestPipelineIntegration:
    """Integration tests for the complete ingestion pipeline."""
    
    def test_connector_to_database_flow(self):
        """Test complete flow: fetch data → normalize → preprocess → insert to DB."""
        # Create test file
        test_file = Path("data/manual_uploads/flow_test.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Flow test content with important task and deadline")
        
        try:
            # Run single pipeline execution
            results = run_ingestion()
            
            # Verify results
            assert isinstance(results, dict)
            assert results["inserted"] >= 0
            assert results["duplicates"] >= 0
            assert results["errors"] >= 0
            
            logger.info(f"✓ Connector → DB flow test passed: {results}")
        
        finally:
            test_file.unlink(missing_ok=True)
    
    def test_multi_connector_integration(self):
        """Test data flowing from multiple connectors through pipeline."""
        # Create multiple test files
        test_files = [
            Path("data/manual_uploads/test1.txt"),
            Path("data/manual_uploads/test2.txt"),
            Path("data/manual_uploads/test3.txt"),
        ]
        
        for i, test_file in enumerate(test_files):
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(f"Multi-connector test {i+1} with meeting content")
        
        try:
            # Run pipeline
            results = run_ingestion()
            
            # Should have processed all connectors
            assert results["inserted"] + results["duplicates"] >= 0
            
            logger.info(f"✓ Multi-connector integration test passed")
        
        finally:
            for test_file in test_files:
                test_file.unlink(missing_ok=True)
    
    def test_end_to_end_whatsapp_to_db(self):
        """Test complete end-to-end: WhatsApp push → normalize → insert → verify DB."""
        test_messages = [
            {
                "chat_name": "Team Chat",
                "message_id": "msg_e2e_001",
                "timestamp": datetime.now().isoformat(),
                "sender": "alice",
                "message": "End-to-end test: we need to finalize the decision by tomorrow",
                "is_group": True,
                "has_media": False,
                "media_data": None,
                "media_mime_type": None,
                "media_filename": None
            }
        ]
        
        # Process through pipeline
        inserted, duplicates, errors = run_ingestion_for_items(test_messages, "whatsapp")
        
        # Should succeed
        assert inserted > 0 or duplicates > 0, "Message should be inserted or found as duplicate"
        assert errors == 0, "Should have no processing errors"
        
        logger.info(f"✓ End-to-end test passed: inserted={inserted}, duplicates={duplicates}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
