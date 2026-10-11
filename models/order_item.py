"""OrderItem domain model."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class OrderItem:
    id: Optional[int]
    order_id: Optional[int]
    menu_item_id: int
    item_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal

    @classmethod
    def create(cls, menu_item_id: int, item_name: str, unit_price: Decimal, quantity: int, order_id: Optional[int] = None) -> "OrderItem":
        line_total = (unit_price * quantity).quantize(Decimal("0.01"))
        return cls(
            id=None,
            order_id=order_id,
            menu_item_id=menu_item_id,
            item_name=item_name,
            unit_price=unit_price,
            quantity=quantity,
            line_total=line_total
        )
