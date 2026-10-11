"""User and UserSettings domain models."""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    role: str = "CASHIER"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def is_admin(self) -> bool:
        return self.role.upper() == "ADMIN"


@dataclass
class UserSettings:
    id: Optional[int]
    user_id: int
    theme: str = "dark"
    currency: str = "₹"
    default_tax_rate: Decimal = Decimal("5.0")
    updated_at: Optional[str] = None
