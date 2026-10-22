"""Automated tests for database management, backup, demo cleanup, and admin recovery suite."""
import sqlite3
import pytest
from pathlib import Path
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from scripts.manage_db import create_backup, get_connection
from utils.security import verify_password


def test_create_backup_file_creation(tmp_path, monkeypatch):
    """Verifies that create_backup safely creates a timestamped copy."""
    test_db = tmp_path / "restaurant.db"
    test_backups = tmp_path / "backups"

    # Initialize a dummy db
    db_mgr = DatabaseManager(test_db)
    initialize_database(db_mgr)

    # Monkeypatch paths
    monkeypatch.setattr("scripts.manage_db.DEFAULT_DB_PATH", test_db)
    monkeypatch.setattr("scripts.manage_db.BACKUPS_DIR", test_backups)

    backup_file = create_backup()
    assert backup_file.exists()
    assert backup_file.parent == test_backups
    assert backup_file.stat().st_size > 0


def test_clean_demo_preserves_master_seeds(tmp_path, monkeypatch):
    """Verifies that clean_demo deletes only orders/bills while preserving master users and menu."""
    from scripts.manage_db import cmd_clean_demo
    import argparse

    test_db = tmp_path / "restaurant.db"
    test_backups = tmp_path / "backups"

    db_mgr = DatabaseManager(test_db)
    initialize_database(db_mgr)

    monkeypatch.setattr("scripts.manage_db.DEFAULT_DB_PATH", test_db)
    monkeypatch.setattr("scripts.manage_db.BACKUPS_DIR", test_backups)
    monkeypatch.setattr("scripts.manage_db.get_connection", lambda: sqlite3.connect(test_db))

    # Insert a dummy order and bill
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("INSERT INTO orders (order_number, user_id, table_number, customer_name, status) VALUES ('ORD-TEST-0001', 1, 'T1', 'Test Cust', 'COMPLETED');")
    ord_id = cur.lastrowid
    cur.execute("INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total) VALUES (?, 1, 'Item 1', 100, 1, 100);", (ord_id,))
    cur.execute("INSERT INTO bills (bill_number, order_id, subtotal, tax_rate, tax_amount, discount_percent, discount_amount, final_total, payment_method, payment_status) VALUES ('BILL-TEST-0001', ?, 100, 5.0, 5.0, 0.0, 0.0, 105.0, 'CASH', 'PAID');", (ord_id,))
    conn.commit()

    # Run clean_demo
    args = argparse.Namespace(confirm=True)
    cmd_clean_demo(args)

    # Verify orders and bills are 0
    cur.execute("SELECT COUNT(*) FROM orders;")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM bills;")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM order_items;")
    assert cur.fetchone()[0] == 0

    # Verify master users and menu items are preserved
    cur.execute("SELECT COUNT(*) FROM users;")
    assert cur.fetchone()[0] == 2
    cur.execute("SELECT COUNT(*) FROM menu_items;")
    assert cur.fetchone()[0] == 26
    conn.close()


def test_recover_admin_resets_password(tmp_path, monkeypatch):
    """Verifies that recover-admin correctly resets the administrator password."""
    from scripts.manage_db import cmd_recover_admin
    import argparse

    test_db = tmp_path / "restaurant.db"
    db_mgr = DatabaseManager(test_db)
    initialize_database(db_mgr)

    monkeypatch.setattr("scripts.manage_db.DEFAULT_DB_PATH", test_db)
    monkeypatch.setattr("scripts.manage_db.get_connection", lambda: sqlite3.connect(test_db))

    # Reset admin password to custom
    new_pw = "NewPlacementPass@2026"
    args = argparse.Namespace(password=new_pw)
    cmd_recover_admin(args)

    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username='admin';")
    pwd_hash = cur.fetchone()[0]
    conn.close()

    assert verify_password(new_pw, pwd_hash) is True
