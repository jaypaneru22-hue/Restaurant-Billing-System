"""Unit tests for domain model dataclasses."""
from decimal import Decimal
from models.user import User, UserSettings
from models.menu_item import MenuItem
from models.order import Order
from models.order_item import OrderItem
from models.bill import Bill


def test_user_model_role_check():
    u_admin = User(id=1, username="admin", password_hash="hash", full_name="Admin", role="ADMIN")
    assert u_admin.is_admin() is True

    u_cashier = User(id=2, username="cashier", password_hash="hash", full_name="Cashier", role="CASHIER")
    assert u_cashier.is_admin() is False


def test_order_item_creation_calculates_line_total():
    item = OrderItem.create(
        menu_item_id=10,
        item_name="Butter Chicken",
        unit_price=Decimal("340.00"),
        quantity=3
    )
    assert item.line_total == Decimal("1020.00")
    assert item.item_name == "Butter Chicken"
    assert item.quantity == 3


def test_order_status_checks():
    order = Order(id=1, order_number="ORD-001", user_id=1, status="PENDING")
    assert order.is_pending() is True
    assert order.is_completed() is False
    assert order.is_cancelled() is False
