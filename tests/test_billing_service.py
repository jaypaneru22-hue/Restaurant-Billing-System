"""Unit and integration tests for BillingService calculations, persistence, and receipts."""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from repositories.billing_repository import BillingRepository
from services.order_service import OrderService
from services.billing_service import BillingService


@pytest.fixture
def billing_fixture(tmp_path):
    db_file = tmp_path / "billing_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    order_repo = OrderRepository(db_manager)
    menu_repo = MenuRepository(db_manager)
    billing_repo = BillingRepository(db_manager)
    order_service = OrderService(order_repo, menu_repo)
    billing_service = BillingService(billing_repo, order_repo)
    return billing_service, order_service, menu_repo, order_repo


def test_calculate_bill_breakdown_precision(billing_fixture):
    service, _, _, _ = billing_fixture
    subtotal = Decimal("1000.00")
    discount = Decimal("10.00")  # 10% discount = 100.00 -> 900.00
    tax = Decimal("5.00")        # 5% tax on 900.00 = 45.00 -> 945.00

    breakdown = service.calculate_bill_breakdown(subtotal, discount, tax)
    assert breakdown["subtotal"] == Decimal("1000.00")
    assert breakdown["discount_amount"] == Decimal("100.00")
    assert breakdown["discounted_subtotal"] == Decimal("900.00")
    assert breakdown["tax_amount"] == Decimal("45.00")
    assert breakdown["final_total"] == Decimal("945.00")


def test_finalize_bill_workflow(billing_fixture):
    service, order_svc, menu_repo, order_repo = billing_fixture
    items = menu_repo.list_all(available_only=True)
    item = items[0]  # price is positive

    # Create an order
    _, _, order = order_svc.create_order(1, "T-10", "Priya", [(item.id, 2)])
    assert order.status == "PENDING"

    # Finalize bill
    ok, msg, bill = service.finalize_bill(order.id, payment_method="UPI", discount_percent_input="5.0", tax_rate_input="5.0")
    assert ok is True
    assert bill is not None
    assert bill.bill_number.startswith("BILL-")
    assert bill.payment_method == "UPI"

    # Verify order is now COMPLETED
    updated_order = order_repo.get_by_id(order.id)
    assert updated_order.status == "COMPLETED"

    # Attempting to re-bill should fail
    ok_second, msg_second, _ = service.finalize_bill(order.id, "CASH")
    assert ok_second is False
    assert "already in 'COMPLETED' status" in msg_second or "already exists" in msg_second


def test_receipt_text_generation(billing_fixture):
    service, order_svc, menu_repo, _ = billing_fixture
    items = menu_repo.list_all(available_only=True)
    _, _, order = order_svc.create_order(1, "T-01", "Rohan", [(items[0].id, 1)])
    _, _, bill = service.finalize_bill(order.id, "CARD")

    receipt = service.format_receipt_text(bill, order)
    assert bill.bill_number in receipt
    assert order.order_number in receipt
    assert "NET PAYABLE AMOUNT:" in receipt
    assert "CARD" in receipt
    assert "Q08 - Improve User Satisfaction" in receipt


def test_historical_price_protection(billing_fixture):
    service, order_svc, menu_repo, order_repo = billing_fixture
    # Add a custom item
    new_item = menu_repo.create("Special Thali", "Main Course", Decimal("200.00"))
    _, _, order = order_svc.create_order(1, "T-08", "Customer", [(new_item.id, 1)])
    _, _, bill = service.finalize_bill(order.id, "CASH")

    assert bill.subtotal == Decimal("200.00")

    # Now change the price of the menu item in catalog to 300.00
    menu_repo.update(new_item.id, "Special Thali", "Main Course", Decimal("300.00"), True)

    # Historical order line items and bill must retain original 200.00
    reloaded_order = order_repo.get_by_id(order.id)
    assert reloaded_order.items[0].unit_price == Decimal("200.00")
    assert reloaded_order.items[0].line_total == Decimal("200.00")

    reloaded_bill = service.get_bill_for_order(order.id)
    assert reloaded_bill.subtotal == Decimal("200.00")
