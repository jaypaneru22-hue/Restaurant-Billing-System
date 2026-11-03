"""Waiter operations service: table assignments, pickup/serving lifecycle, and serving telemetry."""
from typing import Optional, List, Dict, Tuple
from decimal import Decimal
from database.db import DatabaseManager, db
from models.order import Order
from models.user import User
from repositories.order_repository import OrderRepository, order_repository
from repositories.user_repository import UserRepository, user_repository
from utils.logger import logger


class WaiterService:
    """Provides floor waiter order routing, table assignment, and serving tracking."""

    def __init__(
        self,
        db_manager: DatabaseManager = db,
        order_repo: OrderRepository = order_repository,
        user_repo: UserRepository = user_repository
    ):
        self.db = db_manager
        self.order_repo = order_repo
        self.user_repo = user_repo

    def get_all_waiters(self) -> List[User]:
        """Returns all active users with role == 'WAITER'."""
        rows = self.db.fetchall(
            "SELECT id, username, password_hash, full_name, role, is_active, last_login, created_at, updated_at "
            "FROM users WHERE role = 'WAITER' AND is_active = 1 ORDER BY full_name ASC;"
        )
        return [
            User(
                id=r["id"],
                username=r["username"],
                password_hash=r["password_hash"],
                full_name=r["full_name"],
                role=r["role"],
                is_active=bool(r["is_active"]),
                last_login=r["last_login"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )
            for r in rows
        ]

    def get_assigned_tables(self, waiter_id: int) -> List[Dict]:
        """Returns list of restaurant tables currently assigned to this waiter."""
        return self.db.fetchall(
            """
            SELECT t.id, t.table_number, t.zone, t.capacity, t.status, t.active_order_id,
                   t.waiter_id, u.full_name as waiter_name, o.order_number, o.status as order_status
            FROM restaurant_tables t
            LEFT JOIN users u ON t.waiter_id = u.id
            LEFT JOIN orders o ON t.active_order_id = o.id
            WHERE t.waiter_id = ?
            ORDER BY t.table_number ASC;
            """,
            (waiter_id,)
        )

    def get_all_tables_with_waiters(self) -> List[Dict]:
        """Returns all tables with assigned waiter names for Manager overview."""
        return self.db.fetchall(
            """
            SELECT t.id, t.table_number, t.zone, t.capacity, t.status, t.active_order_id,
                   t.waiter_id, u.full_name as waiter_name, u.username as waiter_username
            FROM restaurant_tables t
            LEFT JOIN users u ON t.waiter_id = u.id
            ORDER BY t.table_number ASC;
            """
        )

    def assign_table_to_waiter(self, table_number: str, waiter_id: Optional[int]) -> Tuple[bool, str]:
        """Assigns or clears a waiter assignment for a specific table."""
        try:
            self.db.execute(
                "UPDATE restaurant_tables SET waiter_id = ?, updated_at = CURRENT_TIMESTAMP WHERE table_number = ?;",
                (waiter_id, table_number)
            )
            # If table has an active order, also assign this order to the waiter
            if waiter_id:
                self.db.execute(
                    "UPDATE orders SET waiter_id = ?, updated_at = CURRENT_TIMESTAMP WHERE table_number = ? AND status NOT IN ('COMPLETED', 'CANCELLED');",
                    (waiter_id, table_number)
                )
            logger.info(f"Assigned waiter id={waiter_id} to table {table_number}.")
            return True, f"Table {table_number} assigned successfully."
        except Exception as e:
            logger.error(f"Error assigning table {table_number} to waiter: {e}")
            return False, str(e)

    def get_ready_orders(self) -> List[Dict]:
        """Returns all orders currently marked READY at the kitchen pass waiting for pickup."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.created_at, o.updated_at,
                   u.full_name as waiter_name,
                   (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 as elapsed_ready_mins
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status = 'READY'
            ORDER BY o.updated_at ASC;
        """
        return self.db.fetchall(sql)

    def get_picked_up_orders(self, waiter_id: Optional[int] = None) -> List[Dict]:
        """Returns orders collected from kitchen and currently in delivery."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.picked_up_at, o.created_at,
                   u.full_name as waiter_name,
                   (julianday('now', 'localtime') - julianday(o.picked_up_at)) * 24 * 60 as elapsed_transit_mins
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status = 'PICKED_UP'
        """
        params = []
        if waiter_id is not None:
            sql += " AND o.waiter_id = ?"
            params.append(waiter_id)
        sql += " ORDER BY o.picked_up_at ASC;"
        return self.db.fetchall(sql, tuple(params))

    def get_served_orders(self, waiter_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Returns orders that have been delivered to customer (SERVED)."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.served_at, o.picked_up_at, o.created_at,
                   u.full_name as waiter_name
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status = 'SERVED'
        """
        params = []
        if waiter_id is not None:
            sql += " AND o.waiter_id = ?"
            params.append(waiter_id)
        sql += " ORDER BY o.served_at DESC LIMIT ?;"
        params.append(limit)
        return self.db.fetchall(sql, tuple(params))

    def get_serving_history(self, waiter_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Returns completed serving history (SERVED and COMPLETED)."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.served_at, o.picked_up_at, o.created_at,
                   u.full_name as waiter_name
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status IN ('SERVED', 'COMPLETED')
        """
        params = []
        if waiter_id is not None:
            sql += " AND o.waiter_id = ?"
            params.append(waiter_id)
        sql += " ORDER BY o.id DESC LIMIT ?;"
        params.append(limit)
        return self.db.fetchall(sql, tuple(params))

    def get_delayed_ready_orders(self, threshold_minutes: int = 5) -> List[Dict]:
        """Identifies orders marked READY in kitchen that have been unpicked for > threshold_minutes."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.updated_at,
                   u.full_name as waiter_name,
                   (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 as elapsed_ready_mins
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status = 'READY'
              AND (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 >= ?
            ORDER BY elapsed_ready_mins DESC;
        """
        return self.db.fetchall(sql, (threshold_minutes,))

    def get_waiter_telemetry(self, waiter_id: Optional[int] = None) -> Dict[str, int]:
        """Returns KPI counts for waiter operational dashboard."""
        ready_cnt = len(self.get_ready_orders())
        picked_up_cnt = len(self.get_picked_up_orders(waiter_id=waiter_id))
        served_cnt = len(self.get_served_orders(waiter_id=waiter_id, limit=200))
        tables_cnt = len(self.get_assigned_tables(waiter_id)) if waiter_id else 0
        return {
            "ready_count": ready_cnt,
            "transit_count": picked_up_cnt,
            "served_count": served_cnt,
            "tables_count": tables_cnt
        }


# Global instance
waiter_service = WaiterService()
