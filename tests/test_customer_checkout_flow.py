"""Tests for Customer Order Checkout and Place Order Flow."""
from decimal import Decimal
import pytest
from services.order_service import OrderService
from services.billing_service import BillingService
from services.auth_service import AuthService
from services.menu_service import MenuService
from models.order import Order


@pytest.fixture
def order_svc():
    return OrderService()


@pytest.fixture
def auth_svc():
    return AuthService()


@pytest.fixture
def menu_svc():
    return MenuService()


@pytest.fixture
def billing_svc():
    return BillingService()


def test_customer_checkout_flow_success(order_svc, auth_svc, menu_svc):
    """Test customer places order successfully with special instructions and gets PENDING order."""
    ok, msg, user = auth_svc.login("customer1", "Customer@123")
    assert ok is True
    assert user is not None
    assert user.role == "CUSTOMER"

    items = menu_svc.get_all_items(available_only=True)
    assert len(items) >= 2
    item1 = items[0]
    item2 = items[1]

    item_entries = [(item1.id, 2), (item2.id, 1)]

    ok, err_msg, order = order_svc.create_order(
        user_id=user.id,
        table_number="T3",
        customer_name=user.full_name,
        item_entries=item_entries,
        special_instructions="No spicy, extra ketchup please."
    )

    assert ok is True
    assert order is not None
    assert order.id > 0
    assert order.order_number.startswith("ORD-")
    assert order.status == "PENDING"
    assert order.user_id == user.id
    assert order.table_number == "T3"
    assert order.special_instructions == "No spicy, extra ketchup please."
    assert len(order.items) == 2


def test_customer_order_history_isolation(order_svc, auth_svc, menu_svc):
    """Test that customer only sees their own orders, while staff sees all."""
    ok, _, user1 = auth_svc.login("customer1", "Customer@123")
    assert ok is True
    items = menu_svc.get_all_items(available_only=True)
    item_entries = [(items[0].id, 1)]

    ok, _, order = order_svc.create_order(
        user_id=user1.id,
        table_number="Parcel",
        customer_name=user1.full_name,
        item_entries=item_entries
    )
    assert ok is True

    cust1_orders = order_svc.list_orders(user_id=user1.id)
    assert any(o.id == order.id for o in cust1_orders)
    assert all(o.user_id == user1.id for o in cust1_orders)

    # Different user should not see cust1's orders when filtered
    other_orders = order_svc.list_orders(user_id=999999)
    assert not any(o.id == order.id for o in other_orders)

    # Staff (user_id=None) sees all
    all_orders = order_svc.list_orders(user_id=None)
    assert any(o.id == order.id for o in all_orders)


def test_customer_order_chef_and_billing_integration(order_svc, billing_svc, menu_svc):
    """Test customer order transitions from PENDING -> PREPARING -> COMPLETED through cashier billing."""
    items = menu_svc.get_all_items(available_only=True)
    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T5",
        customer_name="Integration Test Guest",
        item_entries=[(items[0].id, 1)],
        special_instructions="Quick delivery"
    )
    assert ok is True
    assert order.status == "PENDING"

    # Chef updates to PREPARING
    ok, err = order_svc.update_order_status(order.id, "PREPARING")
    assert ok is True

    # Cashier settles bill
    ok, err_msg, bill = billing_svc.finalize_bill(
        order_id=order.id,
        payment_method="CASH",
        discount_percent_input=Decimal("0.00")
    )
    assert ok is True
    assert bill is not None
    assert bill.payment_status == "PAID"

    # Order is now COMPLETED
    updated_order = order_svc.get_order(order.id)
    assert updated_order.status == "COMPLETED"
