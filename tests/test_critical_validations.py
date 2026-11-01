"""Comprehensive regression tests for Critical Billing Validations.

Covers:
1. Empty Order Prevention (service layer, database isolation, UI state).
2. Whole Rupee Menu Item Price Validation (add & edit, Poka-Yoke boundaries).
3. Exact Financial Decimal Billing & Receipt Generation.
"""
import pytest
from decimal import Decimal
from database.db import DatabaseManager
from database.migrations import initialize_database
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from repositories.billing_repository import BillingRepository
from services.order_service import OrderService
from services.menu_service import MenuService
from services.billing_service import BillingService
from utils.validators import validate_price


@pytest.fixture
def validation_fixture(tmp_path):
    db_file = tmp_path / "critical_validation_test.db"
    db_manager = DatabaseManager(db_file)
    initialize_database(db_manager)
    menu_repo = MenuRepository(db_manager)
    order_repo = OrderRepository(db_manager)
    billing_repo = BillingRepository(db_manager)
    menu_svc = MenuService(menu_repo)
    order_svc = OrderService(order_repo, menu_repo)
    billing_svc = BillingService(billing_repo, order_repo)
    return {
        "db": db_manager,
        "menu_repo": menu_repo,
        "order_repo": order_repo,
        "billing_repo": billing_repo,
        "menu_svc": menu_svc,
        "order_svc": order_svc,
        "billing_svc": billing_svc,
    }


# =============================================================================
# 1. EMPTY ORDER PREVENTION TESTS
# =============================================================================

def test_empty_order_creation_is_rejected(validation_fixture):
    """Empty cart checkout must be rejected with exact user-facing message."""
    order_svc = validation_fixture["order_svc"]
    db = validation_fixture["db"]

    initial_count = db.fetchone("SELECT COUNT(*) FROM orders;")[0]

    ok, msg, order = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Test Customer",
        item_entries=[]
    )

    assert ok is False
    assert msg == "Please add at least one item before proceeding."
    assert order is None

    # Verify no record was inserted into SQLite
    final_count = db.fetchone("SELECT COUNT(*) FROM orders;")[0]
    assert final_count == initial_count


def test_order_with_zero_or_negative_quantity_rejected(validation_fixture):
    """Items with 0 or negative quantities must be rejected without creating order."""
    order_svc = validation_fixture["order_svc"]
    menu_repo = validation_fixture["menu_repo"]
    db = validation_fixture["db"]

    item = menu_repo.list_all(available_only=True)[0]
    initial_count = db.fetchone("SELECT COUNT(*) FROM orders;")[0]

    # Test 0 quantity
    ok_zero, msg_zero, order_zero = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Guest",
        item_entries=[(item.id, 0)]
    )
    assert ok_zero is False
    assert "at least 1" in msg_zero
    assert order_zero is None

    # Test negative quantity
    ok_neg, msg_neg, order_neg = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Guest",
        item_entries=[(item.id, -2)]
    )
    assert ok_neg is False
    assert "at least 1" in msg_neg
    assert order_neg is None

    assert db.fetchone("SELECT COUNT(*) FROM orders;")[0] == initial_count


def test_order_with_unavailable_or_invalid_item_rejected(validation_fixture):
    """Unavailable or non-existent items must be rejected."""
    order_svc = validation_fixture["order_svc"]
    menu_repo = validation_fixture["menu_repo"]
    db = validation_fixture["db"]

    initial_count = db.fetchone("SELECT COUNT(*) FROM orders;")[0]

    # Non-existent item ID
    ok_fake, msg_fake, order_fake = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Guest",
        item_entries=[(99999, 1)]
    )
    assert ok_fake is False
    assert "does not exist" in msg_fake
    assert order_fake is None

    # Unavailable item
    disabled_item = menu_repo.create("Disabled Dish", "Starters", Decimal("100.00"), is_available=False)
    ok_unavail, msg_unavail, order_unavail = order_svc.create_order(
        user_id=1,
        table_number="T1",
        customer_name="Guest",
        item_entries=[(disabled_item.id, 1)]
    )
    assert ok_unavail is False
    assert "unavailable" in msg_unavail
    assert order_unavail is None

    assert db.fetchone("SELECT COUNT(*) FROM orders;")[0] == initial_count


def test_cannot_bill_or_generate_receipt_for_empty_order(validation_fixture):
    """BillingService must refuse to create a payment or receipt for an order without items."""
    order_repo = validation_fixture["order_repo"]
    billing_svc = validation_fixture["billing_svc"]
    db = validation_fixture["db"]

    initial_bills = db.fetchone("SELECT COUNT(*) FROM bills;")[0]

    # Attempting to finalize a non-existent or 0-item order
    ok, msg, bill = billing_svc.finalize_bill(order_id=99999, payment_method="CASH")
    assert ok is False
    assert "not found" in msg.lower()
    assert bill is None

    assert db.fetchone("SELECT COUNT(*) FROM bills;")[0] == initial_bills


def test_repository_transaction_rollback_on_empty_items(validation_fixture):
    """OrderRepository.create_order directly raises ValueError if items list is empty."""
    order_repo = validation_fixture["order_repo"]
    with pytest.raises(ValueError, match="Please add at least one item before proceeding."):
        order_repo.create_order(user_id=1, table_number="T1", customer_name="Guest", items=[])


# =============================================================================
# 2. PRICE VALIDATION (WHOLE RUPEES ONLY) TESTS
# =============================================================================

def test_price_validation_accepts_valid_whole_rupees():
    """Valid whole Rupee amounts must be accepted with exact Decimal precision."""
    valid_cases = ["₹10", "₹50", "₹100", "₹250", "₹1,000", 10, 50, 100, 250, 1000]
    for case in valid_cases:
        ok, msg, val = validate_price(case)
        assert ok is True, f"Failed for valid case: {case}"
        assert val is not None
        assert val % 1 == 0


def test_price_validation_rejects_decimals_and_fractions():
    """Prices starting with a decimal or containing decimal fractions must be rejected."""
    # Starting with decimal
    ok_dot, msg_dot, _ = validate_price(".50")
    assert ok_dot is False
    assert "decimal" in msg_dot.lower()

    # Fractional decimal values
    ok_frac1, msg_frac1, _ = validate_price("0.50")
    assert ok_frac1 is False
    assert "decimal" in msg_frac1.lower()

    ok_frac2, msg_frac2, _ = validate_price("10.50")
    assert ok_frac2 is False
    assert "decimal" in msg_frac2.lower()

    ok_float, _, _ = validate_price(10.5)
    assert ok_float is False

    ok_dec, _, _ = validate_price(Decimal("10.50"))
    assert ok_dec is False


def test_price_validation_rejects_zero_negative_empty_and_text():
    """Zero, negative, empty, and non-numeric inputs must be rejected."""
    # Zero
    assert validate_price("₹0")[0] is False
    assert validate_price("0")[0] is False
    assert validate_price(0)[0] is False

    # Negative
    assert validate_price("-50")[0] is False
    assert validate_price(-50)[0] is False

    # Empty
    assert validate_price("")[0] is False
    assert validate_price("   ")[0] is False
    assert validate_price(None)[0] is False

    # Text / Special characters
    assert validate_price("abc")[0] is False
    assert validate_price("fifty")[0] is False
    assert validate_price("@#$")[0] is False


def test_editing_menu_item_cannot_bypass_price_validation(validation_fixture):
    """Editing an existing menu item must strictly enforce whole Rupee validation."""
    menu_svc = validation_fixture["menu_svc"]
    menu_repo = validation_fixture["menu_repo"]

    # 1. Create a valid item priced at ₹100
    ok, msg, item = menu_svc.add_item("Tandoori Platter", "Starters", "100")
    assert ok is True
    assert item.price == Decimal("100.00")

    # 2. Try to update price with decimal fraction 10.50 -> must reject
    ok_edit_dec, msg_edit_dec = menu_svc.update_item(item.id, "Tandoori Platter", "Starters", "10.50", True)
    assert ok_edit_dec is False
    assert "decimal" in msg_edit_dec.lower()

    # 3. Try to update price with .50 -> must reject
    ok_edit_dot, msg_edit_dot = menu_svc.update_item(item.id, "Tandoori Platter", "Starters", ".50", True)
    assert ok_edit_dot is False
    assert "decimal" in msg_edit_dot.lower()

    # 4. Try to update price with -50 -> must reject
    ok_edit_neg, msg_edit_neg = menu_svc.update_item(item.id, "Tandoori Platter", "Starters", "-50", True)
    assert ok_edit_neg is False

    # 5. Verify the item in database retains original valid ₹100.00 price
    reloaded = menu_repo.get_by_id(item.id)
    assert reloaded.price == Decimal("100.00")

    # 6. Valid update with ₹150 must succeed
    ok_valid_update, _ = menu_svc.update_item(item.id, "Tandoori Platter Deluxe", "Starters", "150", True)
    assert ok_valid_update is True
    reloaded_after = menu_repo.get_by_id(item.id)
    assert reloaded_after.price == Decimal("150.00")


# =============================================================================
# 3. BILLING ACCURACY & PAYMENT TESTS
# =============================================================================

def test_multiple_item_totals_and_quantities(validation_fixture):
    """Verifies that multiple item totals, quantities, and Decimal subtotal are exact."""
    menu_svc = validation_fixture["menu_svc"]
    order_svc = validation_fixture["order_svc"]

    ok1, _, item1 = menu_svc.add_item("Dish Alpha", "Main Course", "100")
    ok2, _, item2 = menu_svc.add_item("Dish Beta", "Starters", "50")
    ok3, _, item3 = menu_svc.add_item("Dish Gamma", "Beverages", "250")

    # 2 x 100 (=200) + 3 x 50 (=150) + 1 x 250 (=250) = 600
    ok_ord, _, order = order_svc.create_order(
        user_id=1,
        table_number="T5",
        customer_name="Multi-Item Guest",
        item_entries=[(item1.id, 2), (item2.id, 3), (item3.id, 1)]
    )
    assert ok_ord is True
    assert len(order.items) == 3

    subtotal = sum(i.line_total for i in order.items)
    assert subtotal == Decimal("600.00")


def test_tax_and_discount_calculations_with_payment_and_receipt(validation_fixture):
    """Verifies 10% discount (-60) and 5% GST (+27) on 600 subtotal yielding 567.00 final total."""
    menu_svc = validation_fixture["menu_svc"]
    order_svc = validation_fixture["order_svc"]
    billing_svc = validation_fixture["billing_svc"]

    _, _, dish = menu_svc.add_item("Special Feast", "Main Course", "300")
    ok_ord, _, order = order_svc.create_order(
        user_id=1,
        table_number="T8",
        customer_name="VIP Client",
        item_entries=[(dish.id, 2)]  # Subtotal = 600.00
    )
    assert ok_ord is True

    # Finalize bill with 10% discount and 5% GST
    ok_bill, msg_bill, bill = billing_svc.finalize_bill(
        order_id=order.id,
        payment_method="CASH",
        discount_percent_input=Decimal("10.00"),
        tax_rate_input=Decimal("5.00")
    )
    assert ok_bill is True
    assert bill is not None
    assert bill.subtotal == Decimal("600.00")
    assert bill.discount_amount == Decimal("60.00")       # 10% of 600
    assert bill.tax_amount == Decimal("27.00")            # 5% of 540
    assert bill.final_total == Decimal("567.00")          # 540 + 27
    assert bill.payment_method == "CASH"
    assert bill.payment_status == "PAID"

    # Verify receipt generation includes all details
    receipt_text = billing_svc.format_receipt_text(bill, order)
    assert "TQM GOURMET RESTAURANT" in receipt_text
    assert bill.bill_number in receipt_text
    assert order.order_number in receipt_text
    assert "Special Feast" in receipt_text
    assert "567.00" in receipt_text
    assert "CASH" in receipt_text
