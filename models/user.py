"""User and UserSettings domain models."""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime


@dataclass
class User:
    id: Optional[int]
    username: str
    password_hash: str
    full_name: str
    role: str = "CASHIER"
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def is_admin(self) -> bool:
        return self.role.upper() == "ADMIN"

    def is_manager(self) -> bool:
        return self.role.upper() == "MANAGER"

    def is_cashier(self) -> bool:
        return self.role.upper() == "CASHIER"

    def is_chef(self) -> bool:
        return self.role.upper() == "CHEF"

    def is_customer(self) -> bool:
        return self.role.upper() == "CUSTOMER"

    def format_last_login(self, default_text: str = "Never logged in") -> str:
        """Returns human-readable formatted date and time for last session."""
        if not self.last_login:
            return default_text
        try:
            raw = str(self.last_login).strip().replace("T", " ")
            clean_str = raw.split(".")[0]
            dt = datetime.strptime(clean_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            return str(self.last_login)



@dataclass
class UserSettings:
    id: Optional[int]
    user_id: int
    theme: str = "dark"
    currency: str = "₹"
    default_tax_rate: Decimal = Decimal("5.0")
    updated_at: Optional[str] = None
