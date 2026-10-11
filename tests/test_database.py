"""Unit and integration tests for schema creation and seed migrations."""
import sqlite3
import pytest
from database.db import DatabaseManager
from database.migrations import initialize_database
from utils.security import verify_password


@pytest.fixture
def clean_db(tmp_path):
    db_file = tmp_path / "app_test.db"
    manager = DatabaseManager(db_file)
    initialize_database(manager)
    return manager


def test_schema_tables_exist(clean_db):
    conn = clean_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected_tables = {"users", "user_settings", "menu_items", "orders", "order_items", "bills"}
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' was not found in schema."


def test_seed_initial_users_and_passwords(clean_db):
    conn = clean_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = 'admin';")
    admin_row = cursor.fetchone()
    assert admin_row is not None
    assert admin_row["username"] == "admin"
    assert admin_row["role"] == "ADMIN"
    assert verify_password("Admin@123", admin_row["password_hash"]) is True

    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = 'cashier1';")
    cashier_row = cursor.fetchone()
    assert cashier_row is not None
    assert cashier_row["username"] == "cashier1"
    assert cashier_row["role"] == "CASHIER"
    assert verify_password("Cashier@123", cashier_row["password_hash"]) is True
    conn.close()


def test_seed_menu_items_populated(clean_db):
    conn = clean_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM menu_items;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 20


def test_migrations_idempotency(clean_db):
    # Calling initialize_database a second time must not double rows
    initialize_database(clean_db)
    conn = clean_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    conn.close()
    assert user_count == 2
