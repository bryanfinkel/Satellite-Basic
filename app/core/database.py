# File: app/core/database.py
# Path: Satellite-Basic/app/core/database.py
# Description: Database configuration and session management
# - Handles PostgreSQL/PostGIS connection and initialization
# - Provides session management
# - Configures SQLAlchemy engine
# - Ensures PostGIS extension is installed
# - Implements connection pooling and error handling

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

import logging
from typing import Generator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/satellite_db"
SQLALCHEMY_DATABASE_URL = "postgresql://bryanfinkel:test@localhost/satellite_db"
# Create engine with connection pooling
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verify connection before usage
    pool_size=5,         # Maximum number of permanent connections
    max_overflow=10,     # Maximum number of additional connections
    echo=False          # Set to True for SQL query logging
)

# Initialize PostGIS
def init_postgis() -> None:
    """Initialize PostGIS extension and required schemas"""
    try:
        with engine.connect() as connection:
            # Create schema if it doesn't exist
            connection.execute(text('CREATE SCHEMA IF NOT EXISTS public;'))
            # Create PostGIS extension
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS postgis SCHEMA public;'))
            connection.commit()
            logger.info("PostGIS extension initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostGIS: {str(e)}")
        raise

# Initialize database components
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_postgis() -> str:
    """Verify PostGIS installation and return version"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text('SELECT PostGIS_Version();'))
            version = result.scalar()
            logger.info(f"PostGIS version: {version}")
            return version
    except Exception as e:
        logger.error(f"PostGIS verification failed: {str(e)}")
        raise

# Initialize PostGIS when module is imported
init_postgis()