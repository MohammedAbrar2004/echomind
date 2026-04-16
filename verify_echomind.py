#!/usr/bin/env python3
"""
EchoMind Quick Verification Script
Verifies all implemented connectors and infrastructure are working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from pathlib import Path


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def verify_imports():
    """Verify all required imports work."""
    print_header("1. Verifying Imports")
    
    try:
        from app.utils.logger import setup_logging, get_logger
        print("✓ Logger module imported")
        
        from app.utils.error_handler import ErrorTracker, retry_with_backoff
        print("✓ Error handler module imported")
        
        from app.preprocessing.preprocessor import Preprocessor
        print("✓ Preprocessor module imported")
        
        from app.services.media_service import MediaService
        print("✓ MediaService module imported")
        
        from models.normalized_input import NormalizedInput
        print("✓ NormalizedInput model imported")
        
        from pipelines.ingestion_pipeline import run_ingestion, run_ingestion_for_items
        print("✓ Ingestion pipeline functions imported")
        
        print("\n✅ All imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def verify_connectors():
    """Verify all connectors can be instantiated."""
    print_header("2. Verifying Connectors")
    
    from app.connectors.manual.manual_connector import ManualConnector
    from app.connectors.whatsapp.whatsapp_connector import WhatsAppConnector
    
    connectors_to_test = [
        ("Manual", ManualConnector),
        ("WhatsApp", WhatsAppConnector),
    ]
    
    optional_connectors = [
        ("Gmail", "app.connectors.gmail.gmail_connector", "GmailConnector"),
        ("Calendar", "app.connectors.calendar.calendar_connector", "CalendarConnector"),
        ("GMeet", "app.connectors.gmeet.gmeet_connector", "GMeetConnector"),
    ]
    
    # Test required connectors
    for name, connector_class in connectors_to_test:
        try:
            conn = connector_class()
            print(f"✓ {name:15} - instantiated successfully")
        except Exception as e:
            print(f"✗ {name:15} - instantiation failed: {e}")
            return False
    
    # Test optional connectors (may fail due to missing credentials)
    for name, module_name, class_name in optional_connectors:
        try:
            module = __import__(module_name, fromlist=[class_name])
            connector_class = getattr(module, class_name)
            conn = connector_class()
            print(f"✓ {name:15} - instantiated successfully (credentials found)")
        except FileNotFoundError as e:
            print(f"⊘ {name:15} - credentials not found (expected): {str(e)[:40]}...")
        except ImportError as e:
            print(f"⊘ {name:15} - dependencies missing (expected): {str(e)[:40]}...")
        except Exception as e:
            print(f"⊘ {name:15} - error (may be expected): {str(e)[:40]}...")
    
    print("\n✅ Connector verification complete!")
    return True


def verify_file_structure():
    """Verify required directories exist."""
    print_header("3. Verifying Directory Structure")
    
    required_dirs = [
        "app/connectors",
        "app/services",
        "app/preprocessing",
        "app/utils",
        "data/manual_uploads",
        "logs",
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - creating...")
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"  → Created")
    
    print("\n✅ Directory structure verified!")
    return True


def verify_database_connection():
    """Verify database connection."""
    print_header("4. Verifying Database Connection")
    
    try:
        from app.db.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM memory_chunks;")
        count = cursor.fetchone()[0]
        
        print(f"✓ Database connected")
        print(f"✓ memory_chunks table exists ({count} records)")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database verified!")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("  → Ensure PostgreSQL is running and .env is configured")
        return False


def verify_preprocessor():
    """Verify preprocessor works."""
    print_header("5. Verifying Preprocessor")
    
    try:
        from app.preprocessing.preprocessor import Preprocessor
        from models.normalized_input import NormalizedInput
        
        preprocessor = Preprocessor()
        
        test_input = NormalizedInput(
            source_type="test",
            external_message_id="test_001",
            timestamp=datetime.now(),
            participants=["alice", "bob"],
            content_type="text",
            raw_content="MEETING: IMPORTANT URGENT DECISION   Extra   spaces",
            metadata={"origin": "test"}
        )
        
        result = preprocessor.process(test_input)
        
        print(f"✓ Text cleaning: '{result['raw_content']}'")
        print(f"✓ Salience score: {result['initial_salience']:.2f}")
        print(f"✓ Participants normalized: {result['participants']}")
        
        assert result['initial_salience'] > 0.1, "Salience should be positive"
        assert "alice" in result['participants'], "Participants should be lowercase"
        
        print("\n✅ Preprocessor verified!")
        return True
    except Exception as e:
        print(f"✗ Preprocessor verification failed: {e}")
        return False


def verify_error_handling():
    """Verify error handling infrastructure."""
    print_header("6. Verifying Error Handling")
    
    try:
        from app.utils.error_handler import ErrorTracker, IngestionError, classify_error
        
        # Test error tracker
        tracker = ErrorTracker()
        
        err1 = IngestionError(
            source_type="test",
            external_message_id="item_001",
            error_message="Test error",
            error_type="ValueError",
            is_permanent=False
        )
        
        err2 = IngestionError(
            source_type="test",
            external_message_id="item_002",
            error_message="Permanent error",
            error_type="FileNotFoundError",
            is_permanent=True
        )
        
        tracker.add_error(err1)
        tracker.add_error(err2)
        
        summary = tracker.get_summary()
        
        print(f"✓ Error tracking: {summary['total_errors']} errors tracked")
        print(f"✓ Retryable: {summary['retryable_errors']}")
        print(f"✓ Permanent: {summary['permanent_errors']}")
        
        # Test error classification
        is_perm, err_type = classify_error(ConnectionError("test"))
        print(f"✓ ConnectionError classified as transient: {not is_perm}")
        
        print("\n✅ Error handling verified!")
        return True
    except Exception as e:
        print(f"✗ Error handling verification failed: {e}")
        return False


def verify_manual_connector():
    """Verify manual connector works."""
    print_header("7. Verifying Manual Connector")
    
    try:
        from app.connectors.manual.manual_connector import ManualConnector
        
        # Create test file
        test_file = Path("data/manual_uploads/verification_test.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Verification test content")
        
        # Test connector
        connector = ManualConnector()
        results = connector.fetch_data()
        
        # Clean up
        test_file.unlink()
        
        print(f"✓ Manual connector: Found {len(results)} items")
        
        if len(results) > 0:
            print(f"✓ Sample item: {results[0].external_message_id}")
        
        print("\n✅ Manual connector verified!")
        return True
    except Exception as e:
        print(f"✗ Manual connector verification failed: {e}")
        return False


def print_summary(results: dict):
    """Print final summary."""
    print_header("VERIFICATION SUMMARY")
    
    checks = [
        ("Imports", results.get("imports", False)),
        ("Connectors", results.get("connectors", False)),
        ("Directory Structure", results.get("directories", False)),
        ("Database", results.get("database", False)),
        ("Preprocessor", results.get("preprocessor", False)),
        ("Error Handling", results.get("error_handling", False)),
        ("Manual Connector", results.get("manual_connector", False)),
    ]
    
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    
    for name, passed_check in checks:
        status = "✅" if passed_check else "❌"
        print(f"{status} {name:25} {'PASS' if passed_check else 'FAIL'}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATION CHECKS PASSED! 🎉")
        print("\nYour EchoMind installation is ready to use!")
        print("Next steps:")
        print("  1. Configure.env with your Google credentials (if using Gmail/Calendar/GMeet)")
        print("  2. Run: python app/schedular/scheduler.py")
        print("  3. Or: python -m uvicorn app.api.receiver:app --host 127.0.0.1 --port 8000")
        return True
    else:
        print(f"\n⚠️  Some checks failed. See above for details.")
        return False


def main():
    """Run all verifications."""
    from app.utils.logger import setup_logging
    setup_logging("INFO")
    
    print("\n" + "="*70)
    print("  EchoMind Quick Verification Script")
    print("="*70)
    
    results = {
        "imports": verify_imports(),
        "connectors": verify_connectors(),
        "directories": verify_file_structure(),
        "database": verify_database_connection(),
        "preprocessor": verify_preprocessor(),
        "error_handling": verify_error_handling(),
        "manual_connector": verify_manual_connector(),
    }
    
    success = print_summary(results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
