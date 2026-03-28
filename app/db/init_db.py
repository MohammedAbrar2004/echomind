"""
Database initialization module for EchoMind.
Executes schema.sql to set up the PostgreSQL database.
"""

import os
from connection import get_connection


def init_database():
    """
    Initialize the database by executing schema.sql.
    
    Reads the schema.sql file and executes all SQL statements.
    Commits the transaction if successful, otherwise raises an error.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    
    try:
        # Get database connection
        connection = get_connection()
        cursor = connection.cursor()
        
        # Read and execute schema
        with open(schema_path, "r") as schema_file:
            schema_sql = schema_file.read()
        
        cursor.execute(schema_sql)
        connection.commit()
        
        print("✓ Database schema initialized successfully.")
        
    except FileNotFoundError:
        print(f"✗ Schema file not found at {schema_path}")
        raise
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    init_database()
