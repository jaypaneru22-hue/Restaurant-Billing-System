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
        item_entries: List[Tuple[int, int]],  # List of (menu_item_id, quantity)
        special_instructions: str = ""
    ) -> Tuple[bool, str, Optional[Order]]:
        """Creates a multi-item order with availability validation and line total calculation."""
        if not item_entries:
            return False, "Please add at least one item before proceeding.", None

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

        if not order_items:
            return False, "Please add at least one item before proceeding.", None

        try:
            table = table_number.strip() if table_number and table_number.strip() else "Takeaway"
            customer = customer_name.strip() if customer_name and customer_name.strip() else "Walk-in Customer"
            order = self.order_repo.create_order(
                user_id=user_id,
                table_number=table,
                customer_name=customer,
                items=order_items,
                special_instructions=special_instructions
            )
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

        if not order_items:
            return False, "Please add at least one item before proceeding.", None

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

    def update_order_status(self, order_id: int, status: str) -> Tuple[bool, str]:
        """Updates the status of an order with lifecycle validation."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."
        target_status = status.upper()

        # Lifecycle protection rules
        if target_status == "PICKED_UP" and order.status != "READY":
            return False, f"Cannot pick up order in '{order.status}' status. Order must be READY."
        if target_status == "SERVED" and order.status != "PICKED_UP":
            return False, f"Cannot serve order in '{order.status}' status. Order must be PICKED_UP first."

        success = self.order_repo.update_status(order_id, target_status)
        if success:
            logger.info(f"Order id={order_id} status updated to {target_status}.")
            return True, f"Order status updated to {target_status}."
        return False, "Failed to update order status."

    def assign_waiter_to_order(self, order_id: int, waiter_id: Optional[int]) -> Tuple[bool, str]:
        """Assigns a floor waiter to an active order, validating waiter status."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."

        if waiter_id is not None:
            from repositories.user_repository import UserRepository
            user_repo = UserRepository(self.order_repo.db)
            waiter_user = user_repo.get_by_id(waiter_id)
            if not waiter_user:
                return False, "Selected waiter user not found."
            if not waiter_user.is_active:
                return False, f"Cannot assign order to inactive account '{waiter_user.username}'."
            if not waiter_user.is_waiter():
                return False, f"User '{waiter_user.username}' does not hold the WAITER role."

        ok = self.order_repo.assign_waiter(order_id, waiter_id)
        if ok:
            logger.info(f"Assigned waiter id={waiter_id} to order id={order_id}.")
            return True, f"Waiter assigned to Order #{order.order_number}."
        return False, "Failed to assign waiter."

    def mark_order_picked_up(self, order_id: int, waiter_id: int) -> Tuple[bool, str]:
        """Action: Waiter picks up READY order from kitchen pass (READY -> PICKED_UP)."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."
        if order.status != "READY":
            return False, f"Order #{order.order_number} cannot be picked up because status is '{order.status}' (expected READY)."

        ok = self.order_repo.mark_picked_up(order_id, waiter_id)
        if ok:
            logger.info(f"Order id={order_id} marked as PICKED_UP by waiter id={waiter_id}.")
            try:
                from database.db import db
                db.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES (?, 'ORDER_PICKED_UP', 'SERVICE', ?);",
                    (order.waiter_name or f"waiter_{waiter_id}", f"Collected Order #{order.order_number} from kitchen pass")
                )
            except Exception:
                pass
            return True, f"Order #{order.order_number} picked up from kitchen pass."
        return False, "Failed to mark order as picked up."

    def mark_order_served(self, order_id: int, waiter_id: int) -> Tuple[bool, str]:
        """Action: Waiter delivers order to dining customer (PICKED_UP -> SERVED)."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found."
        if order.status != "PICKED_UP":
            return False, f"Order #{order.order_number} cannot be marked served because status is '{order.status}' (expected PICKED_UP)."

        ok = self.order_repo.mark_served(order_id, waiter_id)
        if ok:
            logger.info(f"Order id={order_id} marked as SERVED by waiter id={waiter_id}.")
            try:
                from database.db import db
                db.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES (?, 'ORDER_SERVED', 'SERVICE', ?);",
                    (order.waiter_name or f"waiter_{waiter_id}", f"Delivered Order #{order.order_number} to table {order.table_number}")
                )
            except Exception:
                pass
            return True, f"Order #{order.order_number} served to table {order.table_number}."
        return False, "Failed to mark order as served."

    def get_order_subtotal(self, order: Order) -> Decimal:
        """Calculates total value of items in order using Decimal."""
        return sum((item.line_total for item in order.items), Decimal("0.00")).quantize(Decimal("0.01"))

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.order_repo.get_by_id(order_id)

    def list_orders(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        user_id: Optional[int] = None,
        waiter_id: Optional[int] = None
    ) -> List[Order]:
        return self.order_repo.list_orders(status=status, limit=limit, user_id=user_id, waiter_id=waiter_id)

    def get_customer_orders(self, user_id: int, limit: int = 50) -> List[Order]:
        """Returns orders strictly belonging to the specified customer."""
        return self.order_repo.list_orders(limit=limit, user_id=user_id)


# Global order service instance
order_service = OrderService()
