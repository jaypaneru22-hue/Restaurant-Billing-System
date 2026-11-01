"""Input validation utilities for Poka-Yoke error prevention."""
from decimal import Decimal, InvalidOperation
from typing import Tuple, Optional
import re
from config.settings import (
    SUPPORTED_PAYMENT_METHODS,
    MAX_DISCOUNT_PERCENT,
    VALID_ORDER_STATUSES,
)


def validate_username(username: str) -> Tuple[bool, str]:
    """Validates username: 3-30 alphanumeric and underscore characters."""
    if not username or not username.strip():
        return False, "Username cannot be empty."
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username may only contain letters, numbers, and underscores."
    return True, "Username is valid."


def validate_price(price_input: str | float | Decimal | int) -> Tuple[bool, str, Optional[Decimal]]:
    """Validates that a price is positive, non-zero, and has at most 2 decimal places."""
    if price_input is None:
        return False, "Price cannot be empty.", None
    try:
        if isinstance(price_input, str):
            price_str = price_input.strip()
            if not price_str:
                return False, "Price cannot be empty.", None
            dec_price = Decimal(price_str)
        else:
            dec_price = Decimal(str(price_input))
    except (InvalidOperation, TypeError, ValueError):
        return False, "Price must be a valid numerical value.", None

    if dec_price <= Decimal("0.00"):
        return False, "Price must be greater than zero.", None

    # Quantize to 2 decimal places to check fraction
    if dec_price.as_tuple().exponent < -2:
        return False, "Price cannot have more than 2 decimal places.", None

    return True, "Price is valid.", dec_price.quantize(Decimal("0.01"))


def validate_menu_item(name: str, category: str, price_input: str | float | Decimal | int) -> Tuple[bool, str, Optional[Decimal]]:
    """Validates menu item attributes: non-empty name, non-empty category, and valid price."""
    if not name or not name.strip():
        return False, "Item name cannot be empty.", None
    clean_name = name.strip()
    if len(clean_name) < 2 or len(clean_name) > 60:
        return False, "Item name must be between 2 and 60 characters.", None

    if not category or not category.strip():
        return False, "Category cannot be empty.", None

    valid_price, err_msg, dec_price = validate_price(price_input)
    if not valid_price:
        return False, err_msg, None

    return True, "Menu item attributes are valid.", dec_price


def validate_quantity(qty_input: int | str) -> Tuple[bool, str, Optional[int]]:
    """Validates that order quantity is an integer >= 1 and <= 999."""
    if qty_input is None:
        return False, "Quantity cannot be empty.", None
    try:
        qty = int(str(qty_input).strip())
    except (ValueError, TypeError):
        return False, "Quantity must be an integer.", None

    if qty < 1:
        return False, "Quantity must be at least 1.", None
    if qty > 999:
        return False, "Quantity cannot exceed 999 per single item line.", None

    return True, "Quantity is valid.", qty


def validate_discount(discount_input: str | float | Decimal | int, max_percent: Decimal = MAX_DISCOUNT_PERCENT) -> Tuple[bool, str, Decimal]:
    """Validates discount percentage: must be between 0.0 and max_percent."""
    if discount_input is None or str(discount_input).strip() == "":
        return True, "No discount applied.", Decimal("0.00")
    try:
        dec_discount = Decimal(str(discount_input).strip())
    except (InvalidOperation, ValueError, TypeError):
        return False, "Discount must be a valid numerical percentage.", Decimal("0.00")

    if dec_discount < Decimal("0.00"):
        return False, "Discount percentage cannot be negative.", Decimal("0.00")
    if dec_discount > max_percent:
        return False, f"Discount cannot exceed maximum allowed of {max_percent}%.", Decimal("0.00")

    return True, "Discount percentage is valid.", dec_discount.quantize(Decimal("0.01"))


def validate_tax_rate(tax_input: str | float | Decimal | int) -> Tuple[bool, str, Decimal]:
    """Validates tax percentage: must be non-negative and <= 50.0%."""
    if tax_input is None or str(tax_input).strip() == "":
        return False, "Tax rate cannot be empty.", Decimal("0.00")
    try:
        dec_tax = Decimal(str(tax_input).strip())
    except (InvalidOperation, ValueError, TypeError):
        return False, "Tax rate must be a valid numerical percentage.", Decimal("0.00")

    if dec_tax < Decimal("0.00") or dec_tax > Decimal("50.00"):
        return False, "Tax rate must be between 0% and 50%.", Decimal("0.00")

    return True, "Tax rate is valid.", dec_tax.quantize(Decimal("0.01"))


def validate_payment_method(method: str) -> Tuple[bool, str]:
    """Validates that the payment method is one of CASH, CARD, UPI."""
    if not method or method.upper() not in SUPPORTED_PAYMENT_METHODS:
        return False, f"Invalid payment method. Must be one of: {', '.join(SUPPORTED_PAYMENT_METHODS)}."
    return True, "Payment method is valid."


def validate_order_status(status: str) -> Tuple[bool, str]:
    """Validates order status."""
    if not status or status.upper() not in VALID_ORDER_STATUSES:
        return False, f"Invalid order status. Must be one of: {', '.join(VALID_ORDER_STATUSES)}."
    return True, "Order status is valid."


def validate_cash_tendered(tendered_input: str | float | Decimal | int, total_due: Decimal) -> Tuple[bool, str, Decimal, Decimal]:
    """Validates tendered cash amount and calculates change due."""
    if tendered_input is None or str(tendered_input).strip() == "":
        return False, "Please enter tendered cash amount.", Decimal("0.00"), Decimal("0.00")
    try:
        tendered = Decimal(str(tendered_input).strip()).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return False, "Tendered cash must be a valid numerical value.", Decimal("0.00"), Decimal("0.00")

    if tendered < Decimal("0.00"):
        return False, "Tendered amount cannot be negative.", Decimal("0.00"), Decimal("0.00")

    if tendered < total_due:
        shortfall = (total_due - tendered).quantize(Decimal("0.01"))
        return False, f"Insufficient cash tendered. Shortfall of ₹{shortfall}.", tendered, Decimal("0.00")

    change_due = (tendered - total_due).quantize(Decimal("0.01"))
    return True, f"Tendered ₹{tendered}. Change due: ₹{change_due}.", tendered, change_due


def validate_demo_card(card_number: str, cardholder_name: str, expiry: str, cvv: str) -> Tuple[bool, str]:
    """Validates simulated demo card inputs without storing or sending sensitive banking data."""
    if not cardholder_name or not cardholder_name.strip():
        return False, "Cardholder name is required for simulated payment."

    clean_num = re.sub(r"[\s\-]", "", card_number or "")
    if not clean_num.isdigit():
        return False, "Card number must contain digits only."
    if len(clean_num) not in (15, 16):
        return False, "Card number must be 15 or 16 digits (e.g. 4532 8812 9011 3456)."

    clean_expiry = (expiry or "").strip()
    if not re.match(r"^(0[1-9]|1[0-2])\/?([0-9]{2})$", clean_expiry):
        return False, "Expiry date must be in MM/YY format (e.g. 12/28)."

    clean_cvv = (cvv or "").strip()
    if not clean_cvv.isdigit() or len(clean_cvv) not in (3, 4):
        return False, "CVV/CVC must be 3 or 4 digits."

    return True, "Simulated card details validated successfully."


def validate_demo_upi(upi_id: str) -> Tuple[bool, str]:
    """Validates simulated Virtual Payment Address (UPI ID) format."""
    if not upi_id or not upi_id.strip():
        return False, "Please enter a simulated UPI ID (e.g. cashier@upi or customer@okhdfcbank)."

    clean_vpa = upi_id.strip()
    if not re.match(r"^[a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9]{2,}$", clean_vpa):
        return False, "Invalid UPI ID format. Format must be username@handle (e.g. demo@okhdfcbank)."

    return True, "Simulated UPI ID validated successfully."

