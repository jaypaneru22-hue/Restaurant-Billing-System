"""Service for customer-isolated dining cart operations."""
from typing import Dict, Any, List, Tuple, Optional
from decimal import Decimal
from repositories.cart_repository import CartRepository
from repositories.menu_repository import MenuRepository
from services.billing_service import billing_service
from utils.logger import logger


class CartService:
    """Provides customer-isolated cart retrieval and pricing calculations."""

    def __init__(
        self,
        cart_repo: Optional[CartRepository] = None,
        menu_repo: Optional[MenuRepository] = None
    ):
        self.cart_repo = cart_repo or CartRepository()
        self.menu_repo = menu_repo or MenuRepository()

    def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """Calculates full cart breakdown with subtotal and estimated tax for the authenticated user."""
        items = self.cart_repo.get_cart_items(user_id)
        subtotal = sum((it["line_total"] for it in items), Decimal("0.00")).quantize(Decimal("0.01"))
        total_items_count = sum((it["quantity"] for it in items), 0)

        tax_rate = billing_service.get_configured_tax_rate()
        tax_amount = (subtotal * (tax_rate / Decimal("100.00"))).quantize(Decimal("0.01"))
        net_total = (subtotal + tax_amount).quantize(Decimal("0.01"))

        return {
            "user_id": user_id,
            "items": items,
            "item_count": total_items_count,
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "net_total": net_total,
            "is_empty": len(items) == 0
        }

    def add_to_cart(self, user_id: int, menu_item_id: int, quantity: int = 1, instructions: str = "") -> Tuple[bool, str]:
        """Adds a dish to the customer's isolated cart after checking availability."""
        if quantity <= 0:
            return False, "Quantity must be at least 1."

        item = self.menu_repo.get_by_id(menu_item_id)
        if not item:
            return False, "Dish not found."
        if not item.is_available:
            return False, f"'{item.name}' is currently 86'd / out of stock."

        self.cart_repo.add_or_update_item(user_id, menu_item_id, quantity, instructions)
        return True, f"Added {quantity}x '{item.name}' to cart."

    def update_cart_item(self, user_id: int, menu_item_id: int, quantity: int) -> Tuple[bool, str]:
        """Modifies line quantity for the customer's cart."""
        self.cart_repo.set_quantity(user_id, menu_item_id, quantity)
        return True, "Cart updated."

    def remove_from_cart(self, user_id: int, menu_item_id: int) -> Tuple[bool, str]:
        """Removes a dish from the customer's cart."""
        self.cart_repo.remove_item(user_id, menu_item_id)
        return True, "Item removed from cart."

    def clear_cart(self, user_id: int) -> Tuple[bool, str]:
        """Empties the customer's cart."""
        self.cart_repo.clear_cart(user_id)
        return True, "Cart cleared."


cart_service = CartService()
