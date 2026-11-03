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
            """
            SELECT o.id, o.order_number, o.user_id, o.table_number, o.customer_name,
                   o.status, o.special_instructions, o.waiter_id, o.picked_up_at, o.served_at,
                   o.created_at, o.updated_at, u.full_name as waiter_name
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.id = ?;
            """,
            (order_id,)
        )
        if not order_row:
            return None
        items = self.get_order_items(order_id)
        special_instructions = order_row["special_instructions"] if "special_instructions" in order_row.keys() and order_row["special_instructions"] else ""
        return Order(
            id=order_row["id"],
            order_number=order_row["order_number"],
            user_id=order_row["user_id"],
            table_number=order_row["table_number"],
            customer_name=order_row["customer_name"],
            status=order_row["status"],
            special_instructions=special_instructions,
            waiter_id=order_row["waiter_id"] if "waiter_id" in order_row.keys() else None,
            waiter_name=order_row["waiter_name"] if "waiter_name" in order_row.keys() else None,
            picked_up_at=order_row["picked_up_at"] if "picked_up_at" in order_row.keys() else None,
            served_at=order_row["served_at"] if "served_at" in order_row.keys() else None,
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

    def create_order(
        self,
        user_id: int,
        table_number: str,
        customer_name: str,
        items: List[OrderItem],
        special_instructions: str = ""
    ) -> Order:
        """Atomically persists an order and its line items."""
        if not items:
            raise ValueError("Please add at least one item before proceeding.")

        from datetime import datetime
        order_number = self.generate_order_number()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO orders (order_number, user_id, table_number, customer_name, status, special_instructions, created_at)
                   VALUES (?, ?, ?, ?, 'PENDING', ?, ?);""",
                (order_number, user_id, table_number.strip(), customer_name.strip(), special_instructions.strip(), created_at)
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

    def assign_waiter(self, order_id: int, waiter_id: int) -> bool:
        """Assigns or reassigns a waiter to an order."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET waiter_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (waiter_id, order_id)
            )
            return cursor.rowcount > 0

    def mark_picked_up(self, order_id: int, waiter_id: int) -> bool:
        """Marks an order as PICKED_UP by waiter."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE orders
                SET status = 'PICKED_UP', waiter_id = ?, picked_up_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (waiter_id, order_id)
            )
            return cursor.rowcount > 0

    def mark_served(self, order_id: int, waiter_id: int) -> bool:
        """Marks an order as SERVED by waiter."""
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE orders
                SET status = 'SERVED', waiter_id = ?, served_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (waiter_id, order_id)
            )
            return cursor.rowcount > 0

    def list_orders(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        user_id: Optional[int] = None,
        waiter_id: Optional[int] = None
    ) -> List[Order]:
        sql = """
            SELECT o.id, o.order_number, o.user_id, o.table_number, o.customer_name,
                   o.status, o.special_instructions, o.waiter_id, o.picked_up_at, o.served_at,
                   o.created_at, o.updated_at, u.full_name as waiter_name
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
        """
        conditions = []
        params = []
        if status and status.strip():
            conditions.append("o.status = ?")
            params.append(status.upper())
        if user_id is not None:
            conditions.append("o.user_id = ?")
            params.append(user_id)
        if waiter_id is not None:
            conditions.append("o.waiter_id = ?")
            params.append(waiter_id)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY o.id DESC LIMIT ?;"
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
                special_instructions=r["special_instructions"] if "special_instructions" in r.keys() and r["special_instructions"] else "",
                waiter_id=r["waiter_id"] if "waiter_id" in r.keys() else None,
                waiter_name=r["waiter_name"] if "waiter_name" in r.keys() else None,
                picked_up_at=r["picked_up_at"] if "picked_up_at" in r.keys() else None,
                served_at=r["served_at"] if "served_at" in r.keys() else None,
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                items=items
            ))
        return orders


order_repository = OrderRepository()
