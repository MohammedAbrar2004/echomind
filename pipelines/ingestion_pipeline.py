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

from app.connectors.whatsapp_connector import WhatsAppConnector
from app.connectors.gmail_connector import GmailConnector
from app.connectors.gmeet_connector import GMeetConnector
from app.connectors.calendar_connector import CalendarConnector
from app.connectors.manual_connector import ManualConnector
from app.connectors.phone_connector import PhoneConnector
from app.preprocessing.preprocessor import Preprocessor
from app.db.connection import get_connection


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
        GmailConnector(),
        GMeetConnector(),
        CalendarConnector(),
        ManualConnector(),
        PhoneConnector()
    ]
    
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
                        
                        # Prepare metadata as JSON string
                        metadata_json = json.dumps(processed_data["metadata"])
                        
                        # Prepare participants as JSON string
                        participants_json = json.dumps(processed_data["participants"])
                        
                        # Insert into database
                        insert_query = """
                            INSERT INTO memory_chunks (
                                user_id,
                                source_id,
                                external_message_id,
                                timestamp,
                                participants,
                                content_type,
                                raw_content,
                                initial_salience,
                                metadata
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(insert_query, (
                            USER_ID,
                            source_id,
                            processed_data["external_message_id"],
                            processed_data["timestamp"],
                            participants_json,
                            processed_data["content_type"],
                            processed_data["raw_content"],
                            processed_data["initial_salience"],
                            metadata_json
                        ))
                        
                        # Commit immediately after each successful insert
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


if __name__ == "__main__":
    run_ingestion()
