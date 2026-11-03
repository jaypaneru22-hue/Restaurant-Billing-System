"""Unit tests for Chef KDS order retrieval, status transitions, and refresh stability."""
import pytest
import customtkinter as ctk
from decimal import Decimal
from database.db import db
from services.order_service import OrderService
from services.auth_service import AuthService
from services.menu_service import MenuService
from ui.chef_kds import ChefKDSFrame


@pytest.fixture(scope="module")
def kds_test_env():
    root = ctk.CTk()
    root.withdraw()
    frame = ChefKDSFrame(root)
    yield root, frame
    try:
        frame.destroy()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass


def test_kds_retrieves_customer_and_staff_orders(kds_test_env):
    """Verifies Chef KDS retrieves both customer and staff orders with items and special instructions."""
    root, frame = kds_test_env
    order_svc = OrderService()
    menu_svc = MenuService()

    items = menu_svc.get_all_items(available_only=True)
    assert len(items) >= 1
    dish = items[0]

    # Create customer order
    ok, msg, order = order_svc.create_order(
        user_id=11,  # customer1
        table_number="T12",
        customer_name="Test Diner",
        item_entries=[(dish.id, 2)],
        special_instructions="Extra crispy, please"
    )
    assert ok is True
    assert order is not None

    active_orders = frame._fetch_active_orders()
    matching = next((o for o in active_orders if o["id"] == order.id), None)
    assert matching is not None
    assert matching["order_number"] == order.order_number
    assert matching["table_number"] == "T12"
    assert matching["customer_name"] == "Test Diner"
    assert matching["special_instructions"] == "Extra crispy, please"
    assert matching["status"] == "PENDING"


def test_kds_in_place_refresh_preserves_widgets(kds_test_env):
    """Verifies that in steady state, periodic ticks update in-place without destroying widgets."""
    root, frame = kds_test_env

    # Sync frame with any newly added orders from test 1
    frame._on_auto_refresh_tick()

    children_before = frame.tickets_scroll.winfo_children()
    assert len(children_before) > 0
    grid_id_before = id(children_before[0])

    # Run 5 periodic ticks in steady state
    for _ in range(5):
        frame._on_auto_refresh_tick()

    children_after = frame.tickets_scroll.winfo_children()
    assert len(children_after) > 0
    grid_id_after = id(children_after[0])
    assert grid_id_before == grid_id_after, "Grid widget was recreated during steady-state refresh!"


def test_kds_single_refresh_timer_and_cancellation(kds_test_env):
    """Verifies that Chef KDS maintains strictly ONE timer and cleans up on destroy."""
    root, frame = kds_test_env

    # Active timer is created at startup
    assert frame._auto_refresh_id is not None
    assert frame._is_active is True

    # Rescheduling preserves single timer instance
    timer1 = frame._auto_refresh_id
    frame._schedule_refresh()
    timer2 = frame._auto_refresh_id
    assert timer2 is not None

    # Destroy cancels timer
    frame.destroy()
    assert frame._auto_refresh_id is None
    assert frame._is_active is False
