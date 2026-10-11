"""Order domain model."""
from dataclasses import dataclass, field
from typing import Optional, List
from models.order_item import OrderItem


@dataclass
class Order:
    id: Optional[int]
    order_number: str
    user_id: int
    table_number: str = "Takeaway"
    customer_name: str = "Walk-in Customer"
    status: str = "PENDING"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)

    def is_pending(self) -> bool:
        return self.status == "PENDING"

    def is_completed(self) -> bool:
        return self.status == "COMPLETED"

    def is_cancelled(self) -> bool:
        return self.status == "CANCELLED"
