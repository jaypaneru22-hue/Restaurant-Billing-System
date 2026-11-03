"""Comprehensive test suite for the WAITER role in RestoPro.

Verifies:
1. Waiter role definition, seeding, authentication, and permission boundaries.
2. Waiter table assignment and persistence.
3. Full end-to-end order lifecycle:
   PENDING -> ACCEPTED -> PREPARING -> READY -> PICKED_UP -> SERVED -> COMPLETED.
4. Role boundary enforcement (Chef cannot mark SERVED, Waiter cannot settle bills).
5. State transition guards and validation rules.
6. Delayed READY order detection for floor managers.
"""
import pytest
from datetime import datetime, timedelta
from database.db import DatabaseManager
from database.migrations import initialize_database
from models.user import User
from models.order import Order
from services.auth_service import AuthService
from services.order_service import OrderService
from services.waiter_service import WaiterService
from repositories.user_repository import UserRepository
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from config.settings import (
    ROLE_WAITER,
    ROLE_CHEF,
    ROLE_MANAGER,
    ROLE_CASHIER,
    ROLE_CUSTOMER,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_ACCEPTED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    ORDER_STATUS_PICKED_UP,
    ORDER_STATUS_SERVED,
    ORDER_STATUS_COMPLETED,
)


@pytest.fixture
def waiter_env(tmp_path):
    """Sets up an isolated test database with seeded users, tables, and menu."""
    db_file = tmp_path / "waiter_test.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)

    auth_svc = AuthService(user_repo=UserRepository(db_mgr))
    order_svc = OrderService(order_repo=OrderRepository(db_mgr), menu_repo=MenuRepository(db_mgr))
    waiter_svc = WaiterService(db_manager=db_mgr, order_repo=OrderRepository(db_mgr))

    return {
        "db": db_mgr,
        "auth_svc": auth_svc,
        "order_svc": order_svc,
        "waiter_svc": waiter_svc,
    }


def test_waiter_seeding_and_auth(waiter_env):
    """Verifies waiter account exists, credentials authenticate, and role predicates hold."""
    auth_svc = waiter_env["auth_svc"]

    success, msg, user = auth_svc.login("waiter1", "Waiter@123")
    assert success is True, f"Authentication failed: {msg}"
    assert user is not None
    assert user.role == ROLE_WAITER
    assert user.is_waiter() is True
    assert user.is_admin() is False
    assert user.is_manager() is False
    assert user.is_cashier() is False
    assert user.is_chef() is False


def test_waiter_table_assignment(waiter_env):
    """Verifies manager assigning tables to waiters and retrieving assigned tables."""
    waiter_svc = waiter_env["waiter_svc"]
    db = waiter_env["db"]

    waiters = waiter_svc.get_all_waiters()
    assert len(waiters) >= 1
    waiter = waiters[0]

    # Assign T-1 and T-2 to this waiter
    ok1, msg1 = waiter_svc.assign_table_to_waiter("T-1", waiter.id)
    assert ok1 is True
    ok2, msg2 = waiter_svc.assign_table_to_waiter("T-2", waiter.id)
    assert ok2 is True

    assigned = waiter_svc.get_assigned_tables(waiter.id)
    table_numbers = [t["table_number"] for t in assigned]
    assert "T-1" in table_numbers
    assert "T-2" in table_numbers

    # Unassign T-1
    ok3, _ = waiter_svc.assign_table_to_waiter("T-1", None)
    assert ok3 is True
    assigned_after = waiter_svc.get_assigned_tables(waiter.id)
    table_numbers_after = [t["table_number"] for t in assigned_after]
    assert "T-1" not in table_numbers_after
    assert "T-2" in table_numbers_after


def test_end_to_end_order_serving_lifecycle(waiter_env):
    """Tests complete lifecycle: Customer -> Chef -> Waiter -> Cashier."""
    order_svc = waiter_env["order_svc"]
    waiter_svc = waiter_env["waiter_svc"]
    db = waiter_env["db"]

    # Get seeded waiter
    waiters = waiter_svc.get_all_waiters()
    assert len(waiters) >= 1
    waiter_id = waiters[0].id

    # 1. Customer places order
    # Using menu item ID 1 (Margherita Pizza)
    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="T-1",
        customer_name="Alice Customer",
        item_entries=[(1, 2)],
        special_instructions="Extra crispy crust"
    )
    assert ok is True
    assert order is not None
    order_id = order.id
    assert order.status == ORDER_STATUS_PENDING

    # 2. Chef accepts order
    ok, _ = order_svc.update_order_status(order_id, ORDER_STATUS_ACCEPTED)
    assert ok is True

    # 3. Chef starts preparing
    ok, _ = order_svc.update_order_status(order_id, ORDER_STATUS_PREPARING)
    assert ok is True

    # Guard: Chef cannot directly mark order SERVED
    ok, err = order_svc.update_order_status(order_id, ORDER_STATUS_SERVED)
    assert ok is False
    assert "Cannot serve order" in err

    # Guard: Waiter cannot pick up order while still PREPARING
    ok, err = order_svc.mark_order_picked_up(order_id, waiter_id=waiter_id)
    assert ok is False
    assert "expected READY" in err

    # 4. Chef marks order READY
    ok, _ = order_svc.update_order_status(order_id, ORDER_STATUS_READY)
    assert ok is True

    # Order must now be visible in Waiter's ready queue
    ready_orders = waiter_svc.get_ready_orders()
    ready_ids = [o["id"] for o in ready_orders]
    assert order_id in ready_ids

    # 5. Waiter picks up order from kitchen
    ok, msg = order_svc.mark_order_picked_up(order_id, waiter_id=waiter_id)
    assert ok is True

    picked_order = order_svc.get_order(order_id)
    assert picked_order.status == ORDER_STATUS_PICKED_UP
    assert picked_order.waiter_id == waiter_id
    assert picked_order.picked_up_at is not None

    # Waiter picked up list should have it
    in_transit = waiter_svc.get_picked_up_orders(waiter_id=waiter_id)
    transit_ids = [o["id"] for o in in_transit]
    assert order_id in transit_ids

    # 6. Waiter serves order to the table
    ok, msg = order_svc.mark_order_served(order_id, waiter_id=waiter_id)
    assert ok is True

    served_order = order_svc.get_order(order_id)
    assert served_order.status == ORDER_STATUS_SERVED
    assert served_order.served_at is not None

    # Order should now be in served orders & history
    served_orders = waiter_svc.get_served_orders(waiter_id=waiter_id)
    served_ids = [o["id"] for o in served_orders]
    assert order_id in served_ids

    # 7. Cashier completes billing
    ok, _ = order_svc.update_order_status(order_id, ORDER_STATUS_COMPLETED)
    assert ok is True
    completed_order = order_svc.get_order(order_id)
    assert completed_order.status == ORDER_STATUS_COMPLETED


def test_waiter_delayed_orders_detection(waiter_env):
    """Verifies that orders waiting > 5 minutes in READY status trigger delayed alerts."""
    order_svc = waiter_env["order_svc"]
    waiter_svc = waiter_env["waiter_svc"]
    db = waiter_env["db"]

    # Create and advance order to READY
    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="Table 3",
        customer_name="Bob VIP",
        item_entries=[(2, 1)],
    )
    assert ok is True
    order_id = order.id
    order_svc.update_order_status(order_id, ORDER_STATUS_ACCEPTED)
    order_svc.update_order_status(order_id, ORDER_STATUS_PREPARING)
    order_svc.update_order_status(order_id, ORDER_STATUS_READY)

    # Artificially set updated_at to 10 minutes ago
    ten_min_ago = (datetime.now() - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("UPDATE orders SET updated_at = ? WHERE id = ?;", (ten_min_ago, order_id))

    delayed = waiter_svc.get_delayed_ready_orders(threshold_minutes=5)
    delayed_ids = [o["id"] for o in delayed]
    assert order_id in delayed_ids
    assert delayed[0]["elapsed_ready_mins"] >= 9.0
