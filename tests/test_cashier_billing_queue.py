"""Automated regression tests for Cashier Billing Queue integration and independent lifecycle statuses."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.billing_repository import BillingRepository
from repositories.menu_repository import MenuRepository
from services.order_service import OrderService
from services.billing_service import BillingService
from services.dashboard_service import DashboardService


@pytest.fixture
def queue_test_env(tmp_path):
    """Provides isolated test database and services."""
    db_file = tmp_path / "test_billing_queue.db"
    db_mgr = DatabaseManager(db_file)
    initialize_database(db_mgr)

    order_repo = OrderRepository(db_mgr)
    billing_repo = BillingRepository(db_mgr)
    menu_repo = MenuRepository(db_mgr)

    order_svc = OrderService(order_repo=order_repo, menu_repo=menu_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)
    dash_svc = DashboardService(db_manager=db_mgr)

    return {
        "db": db_mgr,
        "order_repo": order_repo,
        "billing_repo": billing_repo,
        "menu_repo": menu_repo,
        "order_svc": order_svc,
        "billing_svc": billing_svc,
        "dash_svc": dash_svc
    }


def test_unbilled_order_visible_in_all_serving_states(queue_test_env):
    """Verifies orders remain visible to cashier whether kitchen status is READY or serving status is PICKED_UP or SERVED."""
    order_svc = queue_test_env["order_svc"]
    order_repo = queue_test_env["order_repo"]
    menu_repo = queue_test_env["menu_repo"]

    item = menu_repo.get_by_id(1)

    # 1. Create order (Initial PENDING)
    ok, msg, o1 = order_svc.create_order(
        user_id=1,
        table_number="T-1",
        customer_name="Alice",
        item_entries=[(item.id, 2)]
    )
    assert ok is True

    # PENDING state
    queue = order_svc.get_pending_billing_orders()
    assert len(queue) == 1
    assert queue[0]["id"] == o1.id
    assert queue[0]["kitchen_status"] == "PENDING"
    assert queue[0]["serving_status"] == "IN_KITCHEN"
    assert queue[0]["billing_status"] == "NOT_GENERATED"
    assert queue[0]["payment_status"] == "PENDING"

    # 2. Chef transitions to READY
    order_repo.db.execute("UPDATE orders SET status = 'READY', updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (o1.id,))
    queue_ready = order_svc.get_pending_billing_orders()
    assert len(queue_ready) == 1
    assert queue_ready[0]["kitchen_status"] == "READY"
    assert queue_ready[0]["serving_status"] == "READY"
    assert queue_ready[0]["billing_status"] == "NOT_GENERATED"

    # 3. Waiter transitions to PICKED_UP
    order_repo.db.execute("UPDATE orders SET status = 'PICKED_UP', picked_up_at = CURRENT_TIMESTAMP WHERE id = ?;", (o1.id,))
    queue_picked = order_svc.get_pending_billing_orders()
    assert len(queue_picked) == 1
    assert queue_picked[0]["serving_status"] == "PICKED_UP"
    assert queue_picked[0]["billing_status"] == "NOT_GENERATED"

    # 4. Waiter transitions to SERVED
    order_repo.db.execute("UPDATE orders SET status = 'SERVED', served_at = CURRENT_TIMESTAMP WHERE id = ?;", (o1.id,))
    queue_served = order_svc.get_pending_billing_orders()
    assert len(queue_served) == 1
    assert queue_served[0]["serving_status"] == "SERVED"
    assert queue_served[0]["kitchen_status"] == "READY"
    assert queue_served[0]["billing_status"] == "NOT_GENERATED"


def test_served_order_cashier_bill_generation_and_settlement(queue_test_env):
    """Verifies Cashier generates bill using original Order ID and preserves all customer data."""
    order_svc = queue_test_env["order_svc"]
    billing_svc = queue_test_env["billing_svc"]
    order_repo = queue_test_env["order_repo"]
    menu_repo = queue_test_env["menu_repo"]

    item = menu_repo.get_by_id(1)
    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="Table 1",
        customer_name="Jay",
        item_entries=[(item.id, 1)]
    )
    assert ok is True
    orig_order_id = order.id
    orig_order_number = order.order_number

    # Transition to SERVED
    order_repo.db.execute("UPDATE orders SET status = 'SERVED', served_at = CURRENT_TIMESTAMP WHERE id = ?;", (orig_order_id,))

    # Cashier generates bill
    ok_bill, msg_bill, bill = billing_svc.finalize_bill(
        order_id=orig_order_id,
        payment_method="CASH",
        discount_percent_input=Decimal("0.00"),
        tax_rate_input=Decimal("5.00")
    )
    assert ok_bill is True
    assert bill is not None
    assert bill.order_id == orig_order_id
    assert bill.payment_status == "PAID"

    # Order must be removed from unbilled queue
    unbilled = order_svc.get_pending_billing_orders(filter_status="ALL_UNBILLED")
    assert len(unbilled) == 0

    # Order must appear in settled history with original Order ID
    all_orders = order_svc.get_pending_billing_orders(filter_status="ALL_ORDERS")
    assert len(all_orders) == 1
    assert all_orders[0]["id"] == orig_order_id
    assert all_orders[0]["order_number"] == orig_order_number
    assert all_orders[0]["billing_status"] == "SETTLED"
    assert all_orders[0]["payment_status"] == "PAID"
    assert all_orders[0]["customer_name"] == "Jay"
    assert all_orders[0]["table_number"] == "Table 1"


def test_cancelled_order_excluded_from_cashier_billing(queue_test_env):
    """Verifies cancelled orders are never presented in the cashier billing queue."""
    order_svc = queue_test_env["order_svc"]
    order_repo = queue_test_env["order_repo"]
    menu_repo = queue_test_env["menu_repo"]

    item = menu_repo.get_by_id(1)
    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="T-2",
        customer_name="Bob",
        item_entries=[(item.id, 1)]
    )
    assert ok is True

    # Cancel order
    order_repo.db.execute("UPDATE orders SET status = 'CANCELLED' WHERE id = ?;", (order.id,))

    unbilled = order_svc.get_pending_billing_orders()
    assert len(unbilled) == 0


def test_duplicate_bill_and_payment_prevention(queue_test_env):
    """Verifies system rejects attempts to generate multiple bills for the same order."""
    order_svc = queue_test_env["order_svc"]
    billing_svc = queue_test_env["billing_svc"]
    menu_repo = queue_test_env["menu_repo"]

    item = menu_repo.get_by_id(1)
    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="T-3",
        customer_name="Carol",
        item_entries=[(item.id, 1)]
    )
    assert ok is True

    # First bill succeeds
    ok1, _, bill1 = billing_svc.finalize_bill(order_id=order.id, payment_method="CASH")
    assert ok1 is True

    # Duplicate bill rejected
    ok2, msg2, bill2 = billing_svc.finalize_bill(order_id=order.id, payment_method="CASH")
    assert ok2 is False
    assert "already" in msg2.lower()


def test_billing_queue_filtering_and_search(queue_test_env):
    """Verifies searching by Order ID, Customer Name, and filtering by serving states."""
    order_svc = queue_test_env["order_svc"]
    order_repo = queue_test_env["order_repo"]
    menu_repo = queue_test_env["menu_repo"]

    item = menu_repo.get_by_id(1)

    # Order 1: Served
    _, _, o1 = order_svc.create_order(user_id=1, table_number="T-1", customer_name="David", item_entries=[(item.id, 1)])
    order_repo.db.execute("UPDATE orders SET status = 'SERVED', served_at = CURRENT_TIMESTAMP WHERE id = ?;", (o1.id,))

    # Order 2: Ready
    _, _, o2 = order_svc.create_order(user_id=1, table_number="T-2", customer_name="Emma", item_entries=[(item.id, 2)])
    order_repo.db.execute("UPDATE orders SET status = 'READY' WHERE id = ?;", (o2.id,))

    # Order 3: In transit
    _, _, o3 = order_svc.create_order(user_id=1, table_number="Takeaway", customer_name="Frank", item_entries=[(item.id, 1)])
    order_repo.db.execute("UPDATE orders SET status = 'PICKED_UP', picked_up_at = CURRENT_TIMESTAMP WHERE id = ?;", (o3.id,))

    # Search by customer name
    results_david = order_svc.get_pending_billing_orders(search_query="David")
    assert len(results_david) == 1
    assert results_david[0]["customer_name"] == "David"

    # Search by table number
    results_takeaway = order_svc.get_pending_billing_orders(search_query="Takeaway")
    assert len(results_takeaway) == 1
    assert results_takeaway[0]["customer_name"] == "Frank"

    # Filter by SERVED
    served_only = order_svc.get_pending_billing_orders(filter_status="SERVED")
    assert len(served_only) == 1
    assert served_only[0]["id"] == o1.id

    # Filter by READY
    ready_only = order_svc.get_pending_billing_orders(filter_status="READY")
    assert len(ready_only) == 1
    assert ready_only[0]["id"] == o2.id

    # Filter by ALL_UNBILLED (all 3 unbilled)
    all_unbilled = order_svc.get_pending_billing_orders(filter_status="ALL_UNBILLED")
    assert len(all_unbilled) == 3
    # First item should be SERVED order because of priority ranking
    assert all_unbilled[0]["id"] == o1.id
