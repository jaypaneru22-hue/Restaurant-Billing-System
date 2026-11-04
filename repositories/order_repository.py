"""Repository for orders and order line items persistence."""
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
from database.db import DatabaseManager, db
from models.order import Order
from models.order_item import OrderItem
from utils.logger import logger


class OrderRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def generate_order_number(self, cursor: Optional[sqlite3.Cursor] = None) -> str:
        """Generates a sequential daily order code: ORD-YYYYMMDD-XXXX with collision safety."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"ORD-{today_str}-%"
        if cursor:
            cursor.execute("SELECT order_number FROM orders WHERE order_number LIKE ? ORDER BY id DESC LIMIT 1;", (prefix,))
            row = cursor.fetchone()
        else:
            row = self.db.fetchone("SELECT order_number FROM orders WHERE order_number LIKE ? ORDER BY id DESC LIMIT 1;", (prefix,))
        if row and row[0]:
            try:
                last_seq = int(str(row[0]).split("-")[-1])
                count = last_seq + 1
            except Exception:
                count = 1
        else:
            count = 1
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
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        max_retries = 5
        order_id = None
        for attempt in range(max_retries):
            try:
                with self.db.transaction() as conn:
                    cursor = conn.cursor()
                    order_number = self.generate_order_number(cursor)
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
                # Return outside the transaction block so the transaction is committed
                if order_id:
                    return self.get_by_id(order_id)
            except Exception as e:
                if "UNIQUE constraint failed: orders.order_number" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"Concurrent order number collision detected, retrying (attempt {attempt+1}/{max_retries})...")
                    continue
                raise

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
            if status.upper() == "UNBILLED":
                conditions.append("o.status NOT IN ('COMPLETED', 'CANCELLED')")
            else:
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

    def get_pending_billing_orders(
        self,
        search_query: Optional[str] = None,
        filter_status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves eligible orders for cashier billing with independent business statuses.

        Ensures orders are visible regardless of whether kitchen status is READY or serving status
        is PICKED_UP or SERVED, provided no completed bill has been settled.
        """
        sql = """
            SELECT o.id, o.order_number, o.user_id, o.table_number, o.customer_name,
                   o.status, o.created_at, o.updated_at, o.special_instructions,
                   o.waiter_id, o.picked_up_at, o.served_at,
                   u.full_name AS customer_full_name,
                   w.full_name AS waiter_name,
                   w.username AS waiter_username,
                   b.id AS bill_id, b.bill_number, b.final_total AS bill_final_total,
                   b.payment_status, b.payment_method, b.billed_at,
                   (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS item_count,
                   (SELECT COALESCE(SUM(line_total), 0) FROM order_items WHERE order_id = o.id) AS subtotal
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            LEFT JOIN users w ON o.waiter_id = w.id
            LEFT JOIN bills b ON o.id = b.order_id
            WHERE o.status != 'CANCELLED'
        """
        conditions = []
        params = []

        # Filter handling
        filter_key = (filter_status or "ALL_UNBILLED").upper()
        if filter_key == "ALL_UNBILLED":
            conditions.append("b.id IS NULL AND o.status != 'COMPLETED'")
        elif filter_key == "SERVED":
            conditions.append("b.id IS NULL AND (o.status = 'SERVED' OR o.served_at IS NOT NULL)")
        elif filter_key == "READY":
            conditions.append("b.id IS NULL AND o.status = 'READY'")
        elif filter_key == "PICKED_UP":
            conditions.append("b.id IS NULL AND o.status = 'PICKED_UP'")
        elif filter_key == "IN_KITCHEN":
            conditions.append("b.id IS NULL AND o.status IN ('PENDING', 'NEW', 'ACCEPTED', 'PREPARING')")
        elif filter_key == "BILLED":
            conditions.append("b.id IS NOT NULL")
        elif filter_key == "ALL_ORDERS":
            pass  # return all non-cancelled orders

        if conditions:
            sql += " AND " + " AND ".join(conditions)

        if search_query and search_query.strip():
            sq = f"%{search_query.strip()}%"
            sql += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR o.table_number LIKE ? OR CAST(o.id AS TEXT) = ?)"
            params.extend([sq, sq, sq, search_query.strip()])

        sql += """
            ORDER BY 
                CASE 
                    WHEN b.id IS NULL AND (o.status = 'SERVED' OR o.served_at IS NOT NULL) THEN 1
                    WHEN b.id IS NULL AND o.status = 'READY' THEN 2
                    WHEN b.id IS NULL AND o.status = 'PICKED_UP' THEN 3
                    WHEN b.id IS NULL THEN 4
                    ELSE 5
                END ASC,
                o.id DESC
            LIMIT ?;
        """
        params.append(limit)

        rows = self.db.fetchall(sql, tuple(params))
        results = []
        for r in rows:
            oid = r["id"]
            items = self.get_order_items(oid)
            item_summaries = [f"{it.item_name} ×{it.quantity}" for it in items[:4]]
            if len(items) > 4:
                item_summaries.append(f"+{len(items)-4} more")
            summary_str = ", ".join(item_summaries) if item_summaries else "No items"

            # Independent Status Computation
            # 1. Kitchen Status
            raw_st = r["status"].upper() if r["status"] else "PENDING"
            if raw_st in ("PENDING", "NEW", "RECEIVED"):
                kitchen_status = "PENDING"
            elif raw_st == "ACCEPTED":
                kitchen_status = "ACCEPTED"
            elif raw_st == "PREPARING":
                kitchen_status = "PREPARING"
            elif raw_st in ("READY", "PICKED_UP", "SERVED", "COMPLETED"):
                kitchen_status = "READY"
            else:
                kitchen_status = raw_st

            # 2. Serving Status
            if r["served_at"] is not None or raw_st == "SERVED":
                serving_status = "SERVED"
            elif r["picked_up_at"] is not None or raw_st == "PICKED_UP":
                serving_status = "PICKED_UP"
            elif raw_st == "READY":
                serving_status = "READY"
            else:
                serving_status = "IN_KITCHEN"

            # 3. Billing Status
            if r["bill_id"] is not None:
                bill_status = "SETTLED" if r["payment_status"] == "PAID" or raw_st == "COMPLETED" else "GENERATED"
            else:
                bill_status = "NOT_GENERATED"

            # 4. Payment Status
            if r["bill_id"] is not None and r["payment_status"] == "PAID":
                payment_status = "PAID"
            else:
                payment_status = "PENDING"

            subtotal_val = Decimal(str(r["subtotal"] or "0.00")).quantize(Decimal("0.01"))
            bill_total_val = Decimal(str(r["bill_final_total"])).quantize(Decimal("0.01")) if r["bill_final_total"] is not None else subtotal_val

            results.append({
                "id": oid,
                "order_number": r["order_number"],
                "user_id": r["user_id"],
                "table_number": r["table_number"] or "Takeaway",
                "customer_name": r["customer_name"] or "Walk-in Customer",
                "status": raw_st,
                "kitchen_status": kitchen_status,
                "serving_status": serving_status,
                "billing_status": bill_status,
                "payment_status": payment_status,
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "picked_up_at": r["picked_up_at"],
                "served_at": r["served_at"],
                "special_instructions": r["special_instructions"] or "",
                "waiter_id": r["waiter_id"],
                "waiter_name": r["waiter_name"] or "Unassigned",
                "waiter_username": r["waiter_username"],
                "bill_id": r["bill_id"],
                "bill_number": r["bill_number"],
                "item_count": r["item_count"],
                "items_summary": summary_str,
                "subtotal": subtotal_val,
                "total_amount": bill_total_val,
                "items": items
            })
        return results


order_repository = OrderRepository()
