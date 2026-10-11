"""Order management service enforcing business logic and state transitions."""
from typing import Optional, List, Tuple
from decimal import Decimal
from models.order import Order
from models.order_item import OrderItem
from repositories.order_repository import OrderRepository
from repositories.menu_repository import MenuRepository
from utils.validators import validate_quantity, validate_order_status
from utils.logger import logger


class OrderService:
    def __init__(self, order_repo: Optional[OrderRepository] = None, menu_repo: Optional[MenuRepository] = None):
        self.order_repo = order_repo or OrderRepository()
        self.menu_repo = menu_repo or MenuRepository()

    def create_order(
        self,
        user_id: int,
        table_number: str,
        customer_name: str,
        item_entries: List[Tuple[int, int]]  # List of (menu_item_id, quantity)
    ) -> Tuple[bool, str, Optional[Order]]:
        """Creates a multi-item order with availability validation and line total calculation."""
        if not item_entries:
            return False, "An order must contain at least one menu item.", None

        order_items: List[OrderItem] = []
        for menu_item_id, qty in item_entries:
            valid_qty, qty_msg, quantity = validate_quantity(qty)
            if not valid_qty:
                return False, f"Invalid quantity for item ID {menu_item_id}: {qty_msg}", None

            menu_item = self.menu_repo.get_by_id(menu_item_id)
            if not menu_item:
                return False, f"Menu item ID {menu_item_id} does not exist.", None
            if not menu_item.is_available:
                return False, f"Menu item '{menu_item.name}' is currently unavailable.", None

            order_item = OrderItem.create(
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                unit_price=menu_item.price,
                quantity=quantity
            )
            order_items.append(order_item)

        try:
            table = table_number.strip() if table_number and table_number.strip() else "Takeaway"
            customer = customer_name.strip() if customer_name and customer_name.strip() else "Walk-in Customer"
            order = self.order_repo.create_order(user_id, table, customer, order_items)
            return True, "Order created successfully.", order
        except Exception as e:
            logger.error(f"Error creating order: {e}", exc_info=True)
            return False, f"Database error creating order: {e}", None

    def update_order_items(self, order_id: int, item_entries: List[Tuple[int, int]]) -> Tuple[bool, str]:
        """Updates items for an existing order if still PENDING."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."
        if not order.is_pending():
            return False, f"Cannot modify order in '{order.status}' status. Only PENDING orders can be updated."
        if not item_entries:
            return False, "An order must contain at least one item."

        order_items: List[OrderItem] = []
        for menu_item_id, qty in item_entries:
            valid_qty, qty_msg, quantity = validate_quantity(qty)
            if not valid_qty:
                return False, qty_msg
            menu_item = self.menu_repo.get_by_id(menu_item_id)
            if not menu_item or not menu_item.is_available:
                return False, f"Item ID {menu_item_id} is unavailable."

            order_item = OrderItem.create(
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                unit_price=menu_item.price,
                quantity=quantity,
                order_id=order_id
            )
            order_items.append(order_item)

        try:
            self.order_repo.update_order_items(order_id, order_items)
            return True, "Order items updated successfully."
        except Exception as e:
            logger.error(f"Error updating order items: {e}", exc_info=True)
            return False, f"Database error updating order items: {e}"

    def cancel_order(self, order_id: int) -> Tuple[bool, str]:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."
        if order.status == "COMPLETED":
            return False, "Cannot cancel an already completed and billed order."
        if order.status == "CANCELLED":
            return False, "Order is already cancelled."

        success = self.order_repo.update_status(order_id, "CANCELLED")
        if success:
            logger.info(f"Order id={order_id} marked as CANCELLED.")
            return True, "Order cancelled successfully."
        return False, "Failed to cancel order."

    def get_order_subtotal(self, order: Order) -> Decimal:
        """Calculates total value of items in order using Decimal."""
        return sum((item.line_total for item in order.items), Decimal("0.00")).quantize(Decimal("0.01"))

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.order_repo.get_by_id(order_id)

    def list_orders(self, status: Optional[str] = None, limit: int = 50) -> List[Order]:
        return self.order_repo.list_orders(status=status, limit=limit)


# Global order service instance
order_service = OrderService()
