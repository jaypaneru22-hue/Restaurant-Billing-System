"""Repository for orders and order line items persistence."""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from database.db import DatabaseManager, db
from models.order import Order
from models.order_item import OrderItem
from utils.logger import logger


class OrderRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def generate_order_number(self) -> str:
        """Generates a sequential daily order code: ORD-YYYYMMDD-XXXX."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"ORD-{today_str}-%"
        row = self.db.fetchone(
            "SELECT COUNT(*) FROM orders WHERE order_number LIKE ?;",
            (prefix,)
        )
        count = (row[0] if row else 0) + 1
        return f"ORD-{today_str}-{count:04d}"

    def get_by_id(self, order_id: int) -> Optional[Order]:
        order_row = self.db.fetchone(
            "SELECT id, order_number, user_id, table_number, customer_name, status, created_at, updated_at FROM orders WHERE id = ?;",
            (order_id,)
        )
        if not order_row:
            return None
        items = self.get_order_items(order_id)
        return Order(
            id=order_row["id"],
            order_number=order_row["order_number"],
            user_id=order_row["user_id"],
            table_number=order_row["table_number"],
            customer_name=order_row["customer_name"],
            status=order_row["status"],
            created_at=order_row["created_at"],
            updated_at=order_row["updated_at"],
            items=items
        )

    def get_by_number(self, order_number: str) -> Optional[Order]:
        order_row = self.db.fetchone(
            "SELECT id, order_number, user_id, table_number, customer_name, status, created_at, updated_at FROM orders WHERE order_number = ?;",
            (order_number.strip(),)
        )
        if not order_row:
            return None
        return self.get_by_id(order_row["id"])

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        rows = self.db.fetchall(
            "SELECT id, order_id, menu_item_id, item_name, unit_price, quantity, line_total FROM order_items WHERE order_id = ? ORDER BY id ASC;",
            (order_id,)
        )
        return [
            OrderItem(
                id=r["id"],
                order_id=r["order_id"],
                menu_item_id=r["menu_item_id"],
                item_name=r["item_name"],
                unit_price=Decimal(str(r["unit_price"])),
                quantity=r["quantity"],
                line_total=Decimal(str(r["line_total"]))
            )
            for r in rows
        ]

    def create_order(self, user_id: int, table_number: str, customer_name: str, items: List[OrderItem]) -> Order:
        """Atomically persists an order and its line items."""
        order_number = self.generate_order_number()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO orders (order_number, user_id, table_number, customer_name, status)
                   VALUES (?, ?, ?, ?, 'PENDING');""",
                (order_number, user_id, table_number.strip(), customer_name.strip())
            )
            order_id = cursor.lastrowid

            for item in items:
                cursor.execute(
                    """INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                       VALUES (?, ?, ?, ?, ?, ?);""",
                    (
                        order_id,
                        item.menu_item_id,
                        item.item_name,
                        str(item.unit_price.quantize(Decimal("0.01"))),
                        item.quantity,
                        str(item.line_total.quantize(Decimal("0.01")))
                    )
                )
            logger.info(f"Order created: id={order_id}, order_number={order_number}, total_items={len(items)}")
        return self.get_by_id(order_id)

    def update_order_items(self, order_id: int, items: List[OrderItem]) -> bool:
        """Replaces items for a PENDING order within a transaction."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM order_items WHERE order_id = ?;", (order_id,))
            for item in items:
                cursor.execute(
                    """INSERT INTO order_items (order_id, menu_item_id, item_name, unit_price, quantity, line_total)
                       VALUES (?, ?, ?, ?, ?, ?);""",
                    (
                        order_id,
                        item.menu_item_id,
                        item.item_name,
                        str(item.unit_price.quantize(Decimal("0.01"))),
                        item.quantity,
                        str(item.line_total.quantize(Decimal("0.01")))
                    )
                )
            cursor.execute("UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (order_id,))
            logger.info(f"Updated items for order id={order_id}")
            return True

    def update_status(self, order_id: int, status: str) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (status.upper(), order_id)
            )
            return cursor.rowcount > 0

    def list_orders(self, status: Optional[str] = None, limit: int = 50) -> List[Order]:
        sql = "SELECT id, order_number, user_id, table_number, customer_name, status, created_at, updated_at FROM orders"
        params = []
        if status and status.strip():
            sql += " WHERE status = ?"
            params.append(status.upper())
        sql += " ORDER BY id DESC LIMIT ?;"
        params.append(limit)
        rows = self.db.fetchall(sql, tuple(params))
        orders = []
        for r in rows:
            items = self.get_order_items(r["id"])
            orders.append(Order(
                id=r["id"],
                order_number=r["order_number"],
                user_id=r["user_id"],
                table_number=r["table_number"],
                customer_name=r["customer_name"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                items=items
            ))
        return orders
