"""Test configuration and fixtures."""
import os
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.config import settings


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///test_mars_sandbox.db"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    db_path = Path("test_mars_sandbox.db")
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_session(test_engine):
    """Create a new database session for a test."""
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionTesting()
    
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    yield session
    
    session.close()
    # Drop tables after each test
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db
