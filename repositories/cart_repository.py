"""Repository for persistent, customer-isolated dining shopping carts."""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from database.db import DatabaseManager, db
from utils.logger import logger


class CartRepository:
    """Provides atomic, isolated cart operations keyed by customer user ID."""

    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_cart_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves active cart line items for a specific customer with latest pricing."""
        query = """
            SELECT c.id, c.user_id, c.menu_item_id, c.quantity, c.special_instructions, c.updated_at,
                   m.name as item_name, m.category, m.price as unit_price, m.is_available
            FROM customer_carts c
            JOIN menu_items m ON c.menu_item_id = m.id
            WHERE c.user_id = ?
            ORDER BY c.id ASC;
        """
        rows = self.db.fetchall(query, (user_id,))
        items = []
        for r in rows:
            unit_price = Decimal(str(r["unit_price"]))
            qty = int(r["quantity"])
            items.append({
                "cart_item_id": r["id"],
                "menu_item_id": r["menu_item_id"],
                "item_name": r["item_name"],
                "category": r["category"],
                "unit_price": unit_price,
                "quantity": qty,
                "line_total": (unit_price * qty).quantize(Decimal("0.01")),
                "is_available": bool(r["is_available"]),
                "special_instructions": r["special_instructions"] or ""
            })
        return items

    def add_or_update_item(self, user_id: int, menu_item_id: int, quantity: int, instructions: str = "") -> None:
        """Atomically upserts an item in customer's cart."""
        query = """
            INSERT INTO customer_carts (user_id, menu_item_id, quantity, special_instructions, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, menu_item_id) DO UPDATE SET
                quantity = quantity + excluded.quantity,
                special_instructions = CASE WHEN excluded.special_instructions != '' THEN excluded.special_instructions ELSE customer_carts.special_instructions END,
                updated_at = CURRENT_TIMESTAMP;
        """
        self.db.execute(query, (user_id, menu_item_id, quantity, instructions))

    def set_quantity(self, user_id: int, menu_item_id: int, quantity: int) -> None:
        """Sets exact quantity or deletes item if quantity <= 0."""
        if quantity <= 0:
            self.remove_item(user_id, menu_item_id)
        else:
            query = """
                UPDATE customer_carts
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND menu_item_id = ?;
            """
            self.db.execute(query, (quantity, user_id, menu_item_id))

    def remove_item(self, user_id: int, menu_item_id: int) -> None:
        """Removes a specific dish from customer's cart."""
        query = "DELETE FROM customer_carts WHERE user_id = ? AND menu_item_id = ?;"
        self.db.execute(query, (user_id, menu_item_id))

    def clear_cart(self, user_id: int) -> None:
        """Empties the customer's cart after successful order checkout."""
        query = "DELETE FROM customer_carts WHERE user_id = ?;"
        self.db.execute(query, (user_id,))
