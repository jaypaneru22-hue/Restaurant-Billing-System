"""Unit tests for Poka-Yoke input validators."""
from decimal import Decimal
from utils.validators import (
    validate_username,
    validate_price,
    validate_menu_item,
    validate_quantity,
    validate_discount,
    validate_tax_rate,
    validate_payment_method,
    validate_order_status
)


def test_validate_username():
    ok, _ = validate_username("cashier_01")
    assert ok is True

    bad_short, _ = validate_username("ab")
    assert bad_short is False

    bad_chars, _ = validate_username("user!name@")
    assert bad_chars is False

    empty, _ = validate_username("   ")
    assert empty is False


def test_validate_price():
    ok, _, val = validate_price("149.50")
    assert ok is True
    assert val == Decimal("149.50")

    ok_int, _, val_int = validate_price(250)
    assert ok_int is True
    assert val_int == Decimal("250.00")

    zero_ok, _, _ = validate_price("0.00")
    assert zero_ok is False

    neg_ok, _, _ = validate_price("-10.00")
    assert neg_ok is False

    invalid_str_ok, _, _ = validate_price("abc")
    assert invalid_str_ok is False

    extra_decimals_ok, _, _ = validate_price("10.999")
    assert extra_decimals_ok is False


def test_validate_menu_item():
    ok, _, price = validate_menu_item("Butter Chicken", "Main Course", "320.00")
    assert ok is True
    assert price == Decimal("320.00")

    empty_name, _, _ = validate_menu_item("", "Beverages", "50")
    assert empty_name is False

    empty_cat, _, _ = validate_menu_item("Tea", "", "20")
    assert empty_cat is False


def test_validate_quantity():
    ok, _, qty = validate_quantity(5)
    assert ok is True
    assert qty == 5

    ok_str, _, qty_str = validate_quantity("12")
    assert ok_str is True
    assert qty_str == 12

    zero_ok, _, _ = validate_quantity(0)
    assert zero_ok is False

    neg_ok, _, _ = validate_quantity(-3)
    assert neg_ok is False

    non_int_ok, _, _ = validate_quantity("two")
    assert non_int_ok is False

    huge_ok, _, _ = validate_quantity(1000)
    assert huge_ok is False


def test_validate_discount():
    ok_none, _, d_none = validate_discount("")
    assert ok_none is True
    assert d_none == Decimal("0.00")

    ok_valid, _, d_val = validate_discount("10.0")
    assert ok_valid is True
    assert d_val == Decimal("10.00")

    too_large, _, _ = validate_discount("65.0")
    assert too_large is False

    neg_ok, _, _ = validate_discount("-5")
    assert neg_ok is False


def test_validate_tax_rate():
    ok, _, val = validate_tax_rate("5.0")
    assert ok is True
    assert val == Decimal("5.00")

    neg, _, _ = validate_tax_rate("-1")
    assert neg is False

    exceed, _, _ = validate_tax_rate("60")
    assert exceed is False


def test_validate_payment_method():
    assert validate_payment_method("CASH")[0] is True
    assert validate_payment_method("CARD")[0] is True
    assert validate_payment_method("UPI")[0] is True
    assert validate_payment_method("BITCOIN")[0] is False


def test_validate_order_status():
    assert validate_order_status("PENDING")[0] is True
    assert validate_order_status("COMPLETED")[0] is True
    assert validate_order_status("CANCELLED")[0] is True
    assert validate_order_status("UNKNOWN")[0] is False
