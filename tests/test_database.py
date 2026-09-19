"""
Tests for Database Connection Layer.
"""

from app.database import DatabaseManager, db_manager, get_db


def test_database_manager_initialization():
    mgr = DatabaseManager(uri="mongodb://localhost:27017", db_name="test_health_db")
    assert mgr.db_name == "test_health_db"
    assert mgr.uri == "mongodb://localhost:27017"


def test_database_ping_status():
    status = db_manager.ping()
    assert "status" in status
    assert "database" in status
    # Should safely return status dict without crashing regardless of DB connection state
    assert status["status"] in ["connected", "disconnected", "error"]
