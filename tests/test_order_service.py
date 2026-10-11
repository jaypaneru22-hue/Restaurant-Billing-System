"""Unit tests for OrderService, line items, and state transitions."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from services.order_service import OrderService


@pytest.fixture
def order_fixture(tmp_path):
    db_file = tmp_path / "order_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    order_repo = OrderRepository(db_manager)
    menu_repo = MenuRepository(db_manager)
    service = OrderService(order_repo, menu_repo)
    return service, menu_repo, order_repo


def test_create_order_multiple_items_success(order_fixture):
    service, menu_repo, _ = order_fixture
    items = menu_repo.list_all(available_only=True)
    item1 = items[0]
    item2 = items[1]

    ok, msg, order = service.create_order(
        user_id=1,
        table_number="T-04",
        customer_name="Mr. Sharma",
        item_entries=[(item1.id, 2), (item2.id, 3)]
    )

    assert ok is True
    assert order is not None
    assert order.order_number.startswith("ORD-")
    assert order.status == "PENDING"
    assert len(order.items) == 2
    assert order.items[0].quantity == 2
    assert order.items[1].quantity == 3

    subtotal = service.get_order_subtotal(order)
    expected_subtotal = (item1.price * 2) + (item2.price * 3)
    assert subtotal == expected_subtotal


def test_create_order_empty_items_fails(order_fixture):
    service, _, _ = order_fixture
    ok, msg, order = service.create_order(1, "T-01", "Guest", [])
    assert ok is False
    assert "at least one" in msg
    assert order is None


def test_create_order_unavailable_item_fails(order_fixture):
    service, menu_repo, _ = order_fixture
    new_item = menu_repo.create("Rare Delicacy", "Main Course", Decimal("500.00"), is_available=False)
    ok, msg, order = service.create_order(1, "T-02", "Guest", [(new_item.id, 1)])
    assert ok is False
    assert "currently unavailable" in msg


def test_update_order_items_pending(order_fixture):
    service, menu_repo, _ = order_fixture
    items = menu_repo.list_all(available_only=True)
    _, _, order = service.create_order(1, "T-03", "Guest", [(items[0].id, 1)])

    ok, msg = service.update_order_items(order.id, [(items[0].id, 4), (items[1].id, 2)])
    assert ok is True

    updated_order = service.get_order(order.id)
    assert len(updated_order.items) == 2
    assert updated_order.items[0].quantity == 4


def test_cancel_order_workflow(order_fixture):
    service, menu_repo, _ = order_fixture
    items = menu_repo.list_all(available_only=True)
    _, _, order = service.create_order(1, "T-05", "Guest", [(items[0].id, 1)])

    ok, msg = service.cancel_order(order.id)
    assert ok is True

    cancelled_order = service.get_order(order.id)
    assert cancelled_order.status == "CANCELLED"

    # Cannot modify cancelled order
    ok_mod, msg_mod = service.update_order_items(order.id, [(items[0].id, 2)])
    assert ok_mod is False
    assert "Only PENDING orders" in msg_mod
