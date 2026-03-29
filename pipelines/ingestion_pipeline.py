"""
Ingestion pipeline for EchoMind.
Orchestrates connectors, preprocessing, and database insertion.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2 import errors as psycopg2_errors
import json

from app.connectors.whatsapp.whatsapp_connector import WhatsAppConnector
try:
    from app.connectors.gmail.gmail_connector import GmailConnector
except ImportError:
    # Gmail requires Google API client - skip if not installed
    GmailConnector = None
from app.connectors.gmeet.gmeet_connector import GMeetConnector
from app.connectors.calendar.calendar_connector import CalendarConnector
from app.connectors.manual.manual_connector import ManualConnector
from app.connectors.phone.phone_connector import PhoneConnector
from app.preprocessing.preprocessor import Preprocessor
from app.db.connection import get_connection
from app.db.repository import insert_memory_chunk, insert_media_file


# Mapping of source_type to source_id
SOURCE_ID_MAP = {
    "whatsapp": "39218ef4-b3ce-4b98-b1e2-34afa243c785",
    "gmail": "250f8201-6caa-4b88-8983-b450f8343af6",
    "gmeet": "1c03923e-730c-471b-95a0-4014d000414a",
    "calendar": "a26589c9-8edf-4f44-b7ec-ee5d9e06482e",
    "manual": "2f269226-cc45-4eb8-9c67-7efa8ecb3463",
}

# Dummy user_id for all inserts (prototype)
USER_ID = "5dd97b4c-ab58-4ae7-9fa0-a3d71eef16d9"


def run_ingestion():
    """
    Run the ingestion pipeline across all connectors.
    Preprocesses data and inserts into memory_chunks table.
    """
    connectors = [
        WhatsAppConnector(),
        GmailConnector() if GmailConnector else None,
        GMeetConnector(),
        CalendarConnector(),
        ManualConnector(),
        PhoneConnector()
    ]
    # Filter out None connectors (e.g., Gmail if dependencies not installed)
    connectors = [c for c in connectors if c is not None]
    
    preprocessor = Preprocessor()
    connection = None
    cursor = None
    inserted_count = 0
    duplicate_count = 0
    error_count = 0
    
    try:
        print("=" * 60)
        print("EchoMind Ingestion Pipeline Started")
        print("=" * 60)
        
        # Get database connection
        connection = get_connection()
        cursor = connection.cursor()
        
        # Process each connector
        for connector in connectors:
            connector_name = connector.__class__.__name__
            print(f"\n[{connector_name}] Fetching data...")
            
            try:
                data = connector.fetch_data()
                print(f"  [OK] Retrieved {len(data)} items")
                
                # Process each normalized input
                for normalized_input in data:
                    try:
                        # Preprocess the input
                        processed_data = preprocessor.process(normalized_input)
                        
                        # Get source_id from mapping
                        source_id = SOURCE_ID_MAP.get(processed_data["source_type"])
                        
                        # Insert into database via repository
                        chunk_id = insert_memory_chunk(cursor, {
                            "user_id": USER_ID,
                            "source_id": source_id,
                            "external_message_id": processed_data["external_message_id"],
                            "timestamp": processed_data["timestamp"],
                            "participants": processed_data["participants"],
                            "content_type": processed_data["content_type"],
                            "raw_content": processed_data["raw_content"],
                            "initial_salience": processed_data["initial_salience"],
                            "metadata": processed_data["metadata"]
                        })
                        
                        # Commit after memory_chunk insert
                        connection.commit()
                        
                        # Handle media if present
                        if normalized_input.media:
                            for media_obj in normalized_input.media:
                                insert_media_file(cursor, chunk_id, media_obj, processed_data["source_type"])
                            connection.commit()
                        
                        inserted_count += 1
                        print(f"  [+] Inserted: {processed_data['external_message_id']}")
                    
                    except psycopg2_errors.UniqueViolation:
                        duplicate_count += 1
                        connection.rollback()
                        print(f"  [-] Duplicate skipped: {normalized_input.external_message_id}")
                    
                    except Exception as e:
                        error_count += 1
                        connection.rollback()
                        print(f"  [!] Error processing item: {e}")
            
            except Exception as e:
                print(f"  [!] Error in connector: {e}")
        
        print("\n" + "=" * 60)
        print(f"Ingestion Complete")
        print(f"  Inserted: {inserted_count}")
        print(f"  Duplicates: {duplicate_count}")
        print(f"  Errors: {error_count}")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n[FATAL] Fatal error: {e}")
        if connection:
            connection.rollback()
    
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def run_ingestion_for_items(
    normalized_inputs: list,
    source_type: str
) -> tuple[int, int, int]:
    """
    Run ingestion for a pre-fetched list of NormalizedInput objects.
    Used by the HTTP receiver for push-based connectors.

    Returns:
        tuple: (inserted_count, duplicate_count, error_count)
    """
    preprocessor = Preprocessor()
    connection = None
    cursor = None
    inserted = 0
    duplicates = 0
    errors = 0

    try:
        connection = get_connection()
        cursor = connection.cursor()

        for normalized_input in normalized_inputs:
            try:
                processed_data = preprocessor.process(normalized_input)
                source_id = SOURCE_ID_MAP.get(source_type)

                # Insert memory_chunk via repository
                chunk_id = insert_memory_chunk(cursor, {
                    "user_id": USER_ID,
                    "source_id": source_id,
                    "external_message_id": processed_data["external_message_id"],
                    "timestamp": processed_data["timestamp"],
                    "participants": processed_data["participants"],
                    "content_type": processed_data["content_type"],
                    "raw_content": processed_data["raw_content"],
                    "initial_salience": processed_data["initial_salience"],
                    "metadata": processed_data["metadata"]
                })
                connection.commit()

                # Handle media if present
                if normalized_input.media:
                    for media_obj in normalized_input.media:
                        insert_media_file(cursor, chunk_id, media_obj, source_type)
                    connection.commit()

                inserted += 1

            except psycopg2_errors.UniqueViolation:
                duplicates += 1
                connection.rollback()

            except Exception as e:
                errors += 1
                connection.rollback()
                print(f"[Pipeline] Error inserting item: {e}")

    except Exception as e:
        print(f"[Pipeline] Fatal error: {e}")
        if connection:
            connection.rollback()

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return inserted, duplicates, errors


if __name__ == "__main__":
    run_ingestion()
