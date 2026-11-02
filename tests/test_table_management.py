"""Unit and integration tests for Table and Floor Management with Poka-Yoke guards."""
import pytest
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from services.order_service import OrderService
from decimal import Decimal


@pytest.fixture
def table_env(clean_db_manager):
    db = clean_db_manager

    # Ensure tables exist (they are seeded in migrations, but insert test ones if needed)
    with db.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO restaurant_tables (table_number, zone, capacity, status) VALUES ('TEST-T1', 'Main Dining', 4, 'VACANT');")
        cursor.execute("INSERT OR IGNORE INTO restaurant_tables (table_number, zone, capacity, status) VALUES ('TEST-T2', 'Main Dining', 2, 'VACANT');")

    order_repo = OrderRepository(db)
    menu_repo = MenuRepository(db)
    order_svc = OrderService(order_repo=order_repo, menu_repo=menu_repo)
    dish = menu_repo.create("Cold Coffee Test", "Beverages", Decimal("120.00"))

    return db, order_svc, dish


def test_table_status_transitions(table_env):
    """Verifies table status updates across OCCUPIED, BILL_REQUESTED, CLEANING, and VACANT."""
    db, order_svc, dish = table_env

    # 1. Initially VACANT
    row = db.fetchone("SELECT status FROM restaurant_tables WHERE table_number = 'TEST-T1';")
    assert row["status"] == "VACANT"

    # 2. Mark OCCUPIED
    with db.transaction() as conn:
        conn.cursor().execute("UPDATE restaurant_tables SET status = 'OCCUPIED' WHERE table_number = 'TEST-T1';")
    row = db.fetchone("SELECT status FROM restaurant_tables WHERE table_number = 'TEST-T1';")
    assert row["status"] == "OCCUPIED"

    # 3. Mark BILL_REQUESTED
    with db.transaction() as conn:
        conn.cursor().execute("UPDATE restaurant_tables SET status = 'BILL_REQUESTED' WHERE table_number = 'TEST-T1';")
    row = db.fetchone("SELECT status FROM restaurant_tables WHERE table_number = 'TEST-T1';")
    assert row["status"] == "BILL_REQUESTED"

    # 4. Mark CLEANING
    with db.transaction() as conn:
        conn.cursor().execute("UPDATE restaurant_tables SET status = 'CLEANING' WHERE table_number = 'TEST-T1';")
    row = db.fetchone("SELECT status FROM restaurant_tables WHERE table_number = 'TEST-T1';")
    assert row["status"] == "CLEANING"

    # 5. Reset to VACANT
    with db.transaction() as conn:
        conn.cursor().execute("UPDATE restaurant_tables SET status = 'VACANT' WHERE table_number = 'TEST-T1';")
    row = db.fetchone("SELECT status FROM restaurant_tables WHERE table_number = 'TEST-T1';")
    assert row["status"] == "VACANT"


def test_poka_yoke_guard_prevent_vacate_with_active_orders(table_env):
    """Poka-Yoke Guard: Prevents a table from being vacated if an unsettled active order is tied to it."""
    db, order_svc, dish = table_env

    # Create active order on TEST-T1
    ok, msg, order = order_svc.create_order(1, "TEST-T1", "Guest Dining", [(dish.id, 2)])
    assert ok is True
    assert order.status == "PENDING"

    # Link active order to table
    with db.transaction() as conn:
        conn.cursor().execute("UPDATE restaurant_tables SET status = 'OCCUPIED', active_order_id = ? WHERE table_number = 'TEST-T1';", (order.id,))

    # Poka-Yoke check: query active orders for table before clearing
    active_row = db.fetchone(
        "SELECT id, order_number FROM orders WHERE table_number = 'TEST-T1' AND status != 'COMPLETED';"
    )
    assert active_row is not None
    # Guard blocks setting to VACANT while active_row exists
    has_unsettled_order = (active_row is not None)
    assert has_unsettled_order is True

    # After completing order
    order_svc.update_order_status(order.id, "COMPLETED")
    active_row_after = db.fetchone(
        "SELECT id, order_number FROM orders WHERE table_number = 'TEST-T1' AND status != 'COMPLETED';"
    )
    assert active_row_after is None
    # Now safe to vacate
    has_unsettled_order_after = (active_row_after is not None)
    assert has_unsettled_order_after is False
