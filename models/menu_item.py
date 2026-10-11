"""MenuItem domain model."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class MenuItem:
    id: Optional[int]
    name: str
    category: str
    price: Decimal
    is_available: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "MenuItem":
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            price=Decimal(str(row["price"])),
            is_available=bool(row["is_available"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
