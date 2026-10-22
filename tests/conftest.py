"""Shared pytest configuration, database fixtures, and testing helpers."""
import pytest
from pathlib import Path
from database.db import DatabaseManager
from database.migrations import initialize_database
from services.auth_service import AuthService
from services.menu_service import MenuService
from services.order_service import OrderService
from services.billing_service import BillingService


@pytest.fixture
def test_db_path(tmp_path: Path) -> Path:
    """Provides an isolated temporary SQLite database path."""
    return tmp_path / "app_test.db"


@pytest.fixture
def clean_db_manager(test_db_path: Path) -> DatabaseManager:
    """Initializes a clean database manager with full schema and default seeds."""
    db_mgr = DatabaseManager(test_db_path)
    initialize_database(db_mgr)
    return db_mgr
