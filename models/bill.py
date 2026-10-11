"""Bill domain model representing finalized customer invoices."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Bill:
    id: Optional[int]
    bill_number: str
    order_id: int
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    final_total: Decimal
    payment_method: str
    payment_status: str = "PAID"
    billed_at: Optional[str] = None
