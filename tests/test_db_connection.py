# File: tests/test_db_connection.py
# Path: Satellite-Basic/tests/test_db_connection.py
# Description: Basic database connection test

from app.core.database import engine, verify_postgis
from sqlalchemy import text

def test_connection():
    try:
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful")
            
            # Test PostGIS
            version = verify_postgis()
            print(f"PostGIS version: {version}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()