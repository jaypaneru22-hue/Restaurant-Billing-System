"""Unit and integration tests for Restaurant Profile, Billing/Tax rules, and SQLite Backups."""
import sqlite3
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database


@pytest.fixture
def enterprise_fixture(tmp_path):
    db_file = tmp_path / "enterprise_test.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)
    return {"db": db_mgr, "path": db_file}


def test_restaurant_profile_persistence(enterprise_fixture):
    db_mgr = enterprise_fixture["db"]

    # Initial profile check
    row = db_mgr.fetchone("SELECT * FROM restaurant_profile WHERE id = 1;")
    assert row is not None
    assert "TQM" in row["restaurant_name"]

    # Update profile
    with db_mgr.transaction() as conn:
        conn.execute(
            """UPDATE restaurant_profile
               SET restaurant_name = 'The Grand TQM Palace', gstin = '07TESTGSTIN123'
               WHERE id = 1;"""
        )

    updated = db_mgr.fetchone("SELECT * FROM restaurant_profile WHERE id = 1;")
    assert updated["restaurant_name"] == "The Grand TQM Palace"
    assert updated["gstin"] == "07TESTGSTIN123"


def test_billing_config_persistence(enterprise_fixture):
    db_mgr = enterprise_fixture["db"]

    row = db_mgr.fetchone("SELECT * FROM billing_config WHERE id = 1;")
    assert row is not None
    assert Decimal(str(row["cgst_rate"])) == Decimal("2.5")
    assert Decimal(str(row["sgst_rate"])) == Decimal("2.5")

    # Update rates
    with db_mgr.transaction() as conn:
        conn.execute(
            """UPDATE billing_config
               SET cgst_rate = 6.0, sgst_rate = 6.0, max_discount_percent = 15.0
               WHERE id = 1;"""
        )

    updated = db_mgr.fetchone("SELECT * FROM billing_config WHERE id = 1;")
    assert Decimal(str(updated["cgst_rate"])) == Decimal("6.0")
    assert Decimal(str(updated["sgst_rate"])) == Decimal("6.0")
    assert Decimal(str(updated["max_discount_percent"])) == Decimal("15.0")


def test_audit_log_recording(enterprise_fixture):
    db_mgr = enterprise_fixture["db"]

    with db_mgr.transaction() as conn:
        conn.execute(
            """INSERT INTO audit_logs (username, action, module, details)
               VALUES ('test_admin', 'ROLE_UPDATED', 'ROLES', 'Granted report export to Manager');"""
        )

    log = db_mgr.fetchone("SELECT * FROM audit_logs WHERE username = 'test_admin';")
    assert log is not None
    assert log["action"] == "ROLE_UPDATED"
    assert log["module"] == "ROLES"


def test_sqlite_online_backup(enterprise_fixture, tmp_path):
    src_path = enterprise_fixture["path"]
    dst_path = tmp_path / "snapshot.bak"

    src_conn = sqlite3.connect(src_path)
    dst_conn = sqlite3.connect(dst_path)
    with dst_conn:
        src_conn.backup(dst_conn)
    src_conn.close()
    dst_conn.close()

    assert dst_path.exists()
    assert dst_path.stat().st_size > 0

    # Verify integrity of backup
    check_conn = sqlite3.connect(dst_path)
    res = check_conn.execute("PRAGMA integrity_check;").fetchone()[0]
    check_conn.close()
    assert res == "ok"


def test_roles_permissions_matrix(enterprise_fixture):
    db_mgr = enterprise_fixture["db"]

    # Insert an override permission
    with db_mgr.transaction() as conn:
        conn.execute(
            """INSERT INTO roles_permissions (role, module, permission_key, is_granted)
               VALUES ('MANAGER', 'REPORTS', 'reports_export_csv', 1)
               ON CONFLICT(role, module, permission_key) DO UPDATE SET is_granted = excluded.is_granted;"""
        )

    row = db_mgr.fetchone(
        "SELECT is_granted FROM roles_permissions WHERE role = 'MANAGER' AND permission_key = 'reports_export_csv';"
    )
    assert row is not None
    assert row["is_granted"] == 1


def test_sales_csv_export(enterprise_fixture, tmp_path):
    import csv
    db_mgr = enterprise_fixture["db"]

    # Seed an order and bill
    with db_mgr.transaction() as conn:
        conn.execute(
            """INSERT INTO orders (order_number, user_id, table_number, customer_name, status)
               VALUES ('ORD-TEST-01', 1, 'T-1', 'Rajesh Sharma', 'COMPLETED');"""
        )
        order_id = conn.execute("SELECT last_insert_rowid();").fetchone()[0]
        conn.execute(
            f"""INSERT INTO bills (bill_number, order_id, subtotal, tax_amount, discount_amount, final_total, payment_method)
               VALUES ('BILL-TEST-01', {order_id}, 400.0, 50.0, 0.0, 450.0, 'UPI');"""
        )

    # Perform CSV export logic matching ui/reports.py
    export_csv = tmp_path / "sales_test.csv"
    rows = db_mgr.fetchall(
        """SELECT b.bill_number, b.final_total, b.tax_amount, b.discount_amount,
                  b.payment_method, b.billed_at, o.order_number, o.table_number, o.customer_name
           FROM bills b
           JOIN orders o ON b.order_id = o.id
           ORDER BY b.id DESC;"""
    )
    assert len(rows) >= 1

    with open(export_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Bill Number", "Order Number", "Table", "Customer", "Payment Method", "Discount", "Tax", "Total", "Created At"])
        for r in rows:
            writer.writerow([r["bill_number"], r["order_number"], r["table_number"], r["customer_name"], r["payment_method"], r["discount_amount"], r["tax_amount"], r["final_total"], r["billed_at"]])

    assert export_csv.exists()
    assert export_csv.stat().st_size > 0
    with open(export_csv, mode="r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) >= 2  # header + row
        assert reader[0][0] == "Bill Number"
        assert reader[1][0] == "BILL-TEST-01"

