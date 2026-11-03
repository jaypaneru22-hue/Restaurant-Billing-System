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
    special_instructions: str = ""
    waiter_id: Optional[int] = None
    waiter_name: Optional[str] = None
    picked_up_at: Optional[str] = None
    served_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)

    def is_pending(self) -> bool:
        return self.status == "PENDING"

    def is_ready(self) -> bool:
        return self.status == "READY"

    def is_picked_up(self) -> bool:
        return self.status == "PICKED_UP"

    def is_served(self) -> bool:
        return self.status == "SERVED"

    def is_completed(self) -> bool:
        return self.status == "COMPLETED"

    def is_cancelled(self) -> bool:
        return self.status == "CANCELLED"
