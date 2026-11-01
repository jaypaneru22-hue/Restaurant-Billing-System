"""Automated tests for POS Payment Workflow and Input Validation."""
import pytest
from decimal import Decimal
from services.billing_service import BillingService
from services.order_service import OrderService
from repositories.billing_repository import BillingRepository
from repositories.order_repository import OrderRepository
from utils.validators import (
    validate_cash_tendered,
    validate_demo_card,
    validate_demo_upi,
    validate_payment_method,
)
from config.settings import ORDER_STATUS_PENDING, ORDER_STATUS_COMPLETED


def test_validate_cash_tendered_exact():
    ok, msg, tendered, change = validate_cash_tendered("250.00", Decimal("250.00"))
    assert ok is True
    assert tendered == Decimal("250.00")
    assert change == Decimal("0.00")


def test_validate_cash_tendered_excess():
    ok, msg, tendered, change = validate_cash_tendered("500", Decimal("350.50"))
    assert ok is True
    assert tendered == Decimal("500.00")
    assert change == Decimal("149.50")


def test_validate_cash_tendered_insufficient():
    ok, msg, tendered, change = validate_cash_tendered("200.00", Decimal("250.00"))
    assert ok is False
    assert "Shortfall" in msg
    assert change == Decimal("0.00")


def test_validate_cash_tendered_invalid():
    ok, msg, _, _ = validate_cash_tendered("abc", Decimal("100.00"))
    assert ok is False


def test_validate_demo_card_valid():
    ok, msg = validate_demo_card(
        card_number="4532 8812 9011 3456",
        cardholder_name="Jay Paneru",
        expiry="12/28",
        cvv="888"
    )
    assert ok is True


def test_validate_demo_card_missing_name():
    ok, msg = validate_demo_card(
        card_number="4532 8812 9011 3456",
        cardholder_name="",
        expiry="12/28",
        cvv="888"
    )
    assert ok is False
    assert "name is required" in msg.lower()


def test_validate_demo_card_invalid_number():
    ok, msg = validate_demo_card(
        card_number="1234",
        cardholder_name="Jay Paneru",
        expiry="12/28",
        cvv="888"
    )
    assert ok is False
    assert "15 or 16 digits" in msg


def test_validate_demo_card_invalid_expiry():
    ok, msg = validate_demo_card(
        card_number="4532 8812 9011 3456",
        cardholder_name="Jay Paneru",
        expiry="99/99",
        cvv="888"
    )
    assert ok is False
    assert "MM/YY" in msg


def test_validate_demo_card_invalid_cvv():
    ok, msg = validate_demo_card(
        card_number="4532 8812 9011 3456",
        cardholder_name="Jay Paneru",
        expiry="12/28",
        cvv="12"
    )
    assert ok is False
    assert "CVV" in msg


def test_validate_demo_upi_valid():
    ok, msg = validate_demo_upi("cashier@okhdfcbank")
    assert ok is True
    ok2, msg2 = validate_demo_upi("guest@upi")
    assert ok2 is True


def test_validate_demo_upi_invalid():
    ok, msg = validate_demo_upi("invalid_upi_without_at")
    assert ok is False
    assert "format" in msg.lower()


def test_cash_payment_finalization(clean_db_manager):
    order_repo = OrderRepository(db_manager=clean_db_manager)
    billing_repo = BillingRepository(db_manager=clean_db_manager)
    order_svc = OrderService(order_repo=order_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)

    # Create pending order
    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Cash Guest",
        item_entries=[(1, 2)]  # 2 x Masala Chai (25.00) = 50.00
    )
    assert ok is True
    assert order.status == ORDER_STATUS_PENDING

    # Finalize with CASH
    f_ok, f_msg, bill = billing_svc.finalize_bill(
        order_id=order.id,
        payment_method="CASH",
        discount_percent_input="0",
        tax_rate_input="5.0"
    )
    assert f_ok is True
    assert bill is not None
    assert bill.payment_method == "CASH"

    # Verify order is COMPLETED
    updated_order = order_svc.get_order(order.id)
    assert updated_order.status == ORDER_STATUS_COMPLETED


def test_demo_card_payment_finalization(clean_db_manager):
    order_repo = OrderRepository(db_manager=clean_db_manager)
    billing_repo = BillingRepository(db_manager=clean_db_manager)
    order_svc = OrderService(order_repo=order_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)

    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T2",
        customer_name="Card Guest",
        item_entries=[(2, 1)]  # 1 x Paneer Butter Masala
    )
    assert ok is True

    f_ok, f_msg, bill = billing_svc.finalize_bill(
        order_id=order.id,
        payment_method="CARD",
        discount_percent_input="10.0",
        tax_rate_input="5.0"
    )
    assert f_ok is True
    assert bill.payment_method == "CARD"
    assert bill.discount_percent == Decimal("10.00")

    updated_order = order_svc.get_order(order.id)
    assert updated_order.status == ORDER_STATUS_COMPLETED


def test_demo_upi_payment_finalization(clean_db_manager):
    order_repo = OrderRepository(db_manager=clean_db_manager)
    billing_repo = BillingRepository(db_manager=clean_db_manager)
    order_svc = OrderService(order_repo=order_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)

    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T3",
        customer_name="UPI Guest",
        item_entries=[(1, 1)]
    )
    assert ok is True

    f_ok, f_msg, bill = billing_svc.finalize_bill(
        order_id=order.id,
        payment_method="UPI",
        discount_percent_input="0",
        tax_rate_input="5.0"
    )
    assert f_ok is True
    assert bill.payment_method == "UPI"

    updated_order = order_svc.get_order(order.id)
    assert updated_order.status == ORDER_STATUS_COMPLETED


def test_payment_cancellation_leaves_order_pending(clean_db_manager):
    order_repo = OrderRepository(db_manager=clean_db_manager)
    billing_repo = BillingRepository(db_manager=clean_db_manager)
    order_svc = OrderService(order_repo=order_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)

    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T4",
        customer_name="Cancel Guest",
        item_entries=[(1, 1)]
    )
    assert ok is True

    # User cancels payment (no finalize_bill called)
    existing_bill = billing_svc.get_bill_for_order(order.id)
    assert existing_bill is None

    curr_order = order_svc.get_order(order.id)
    assert curr_order.status == ORDER_STATUS_PENDING


def test_duplicate_payment_prevention(clean_db_manager):
    order_repo = OrderRepository(db_manager=clean_db_manager)
    billing_repo = BillingRepository(db_manager=clean_db_manager)
    order_svc = OrderService(order_repo=order_repo)
    billing_svc = BillingService(billing_repo=billing_repo, order_repo=order_repo)

    ok, _, order = order_svc.create_order(
        user_id=1,
        table_number="T5",
        customer_name="Double Bill Guest",
        item_entries=[(1, 1)]
    )
    assert ok is True

    # First settlement
    f_ok, _, bill1 = billing_svc.finalize_bill(order.id, "CASH")
    assert f_ok is True

    # Second settlement attempt must fail
    f_ok2, msg2, bill2 = billing_svc.finalize_bill(order.id, "CASH")
    assert f_ok2 is False
    assert "already in 'COMPLETED' status" in msg2 or "already exists" in msg2
