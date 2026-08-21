import pytest
from app.memory.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize the test database before running any tests"""
    init_db()
    yield
