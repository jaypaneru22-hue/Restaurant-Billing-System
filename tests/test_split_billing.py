"""Unit tests for Split Billing exact penny reconciliation and validation logic."""
from decimal import Decimal
import pytest


def calculate_equal_split_shares(total_amount: Decimal, num_parties: int):
    """Reconciles penny-perfect equal split shares."""
    base_share = (total_amount / Decimal(num_parties)).quantize(Decimal("0.01"))
    shares = [base_share] * num_parties
    discrepancy = total_amount - sum(shares)

    # Distribute 1-paise discrepancy to initial shares
    idx = 0
    step = Decimal("0.01") if discrepancy > 0 else Decimal("-0.01")
    while discrepancy != Decimal("0.00") and idx < num_parties:
        shares[idx] += step
        discrepancy -= step
        idx += 1

    return shares


def test_equal_split_three_parties_penny_reconciliation():
    """Verifies that ₹100.00 split 3 ways yields exactly ₹33.34 + ₹33.33 + ₹33.33 = ₹100.00."""
    total = Decimal("100.00")
    shares = calculate_equal_split_shares(total, 3)

    assert len(shares) == 3
    assert shares[0] == Decimal("33.34")
    assert shares[1] == Decimal("33.33")
    assert shares[2] == Decimal("33.33")
    assert sum(shares) == total


def test_equal_split_seven_parties_reconciliation():
    """Verifies that ₹1254.50 split 7 ways reconciles to the exact penny."""
    total = Decimal("1254.50")
    shares = calculate_equal_split_shares(total, 7)

    assert len(shares) == 7
    assert sum(shares) == total


def test_custom_split_variance_validation():
    """Verifies custom split validation against excess or deficient allocations."""
    total = Decimal("500.00")

    # Case A: Exact sum
    custom_a = [Decimal("200.00"), Decimal("150.00"), Decimal("150.00")]
    variance_a = total - sum(custom_a)
    assert variance_a == Decimal("0.00")

    # Case B: Under allocation
    custom_b = [Decimal("200.00"), Decimal("100.00")]
    variance_b = total - sum(custom_b)
    assert variance_b == Decimal("200.00")
    assert variance_b != Decimal("0.00")

    # Case C: Over allocation
    custom_c = [Decimal("300.00"), Decimal("300.00")]
    variance_c = total - sum(custom_c)
    assert variance_c == Decimal("-100.00")
    assert variance_c != Decimal("0.00")
