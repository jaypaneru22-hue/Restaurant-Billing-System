"""Waiter operations service: table assignments, pickup/serving lifecycle, customer assistance requests, and serving telemetry."""
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from decimal import Decimal
from database.db import DatabaseManager, db
from models.order import Order
from models.user import User
from repositories.order_repository import OrderRepository, order_repository
from repositories.user_repository import UserRepository, user_repository
from utils.logger import logger


class WaiterService:
    """Provides floor waiter order routing, table assignment, customer requests, and serving tracking."""

    def __init__(
        self,
        db_manager: DatabaseManager = db,
        order_repo: OrderRepository = order_repository,
        user_repo: UserRepository = user_repository
    ):
        self.db = db_manager
        self.order_repo = order_repo
        self.user_repo = user_repo

    def get_all_waiters(self, active_only: bool = True) -> List[User]:
        """Returns all users with role == 'WAITER'."""
        sql = "SELECT id, username, password_hash, full_name, role, is_active, last_login, created_at, updated_at FROM users WHERE role = 'WAITER'"
        if active_only:
            sql += " AND is_active = 1"
        sql += " ORDER BY full_name ASC;"
        rows = self.db.fetchall(sql)
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
        """Returns list of restaurant tables currently assigned to this waiter with active order & request details."""
        return self.db.fetchall(
            """
            SELECT t.id, t.table_number, t.zone, t.capacity, t.status, t.active_order_id,
                   t.waiter_id, u.full_name as waiter_name, o.order_number, o.status as order_status,
                   o.customer_name as active_customer_name,
                   (SELECT COUNT(*) FROM service_requests sr WHERE sr.table_number = t.table_number AND sr.status IN ('PENDING', 'IN_PROGRESS')) as pending_requests_count
            FROM restaurant_tables t
            LEFT JOIN users u ON t.waiter_id = u.id
            LEFT JOIN orders o ON t.active_order_id = o.id
            WHERE t.waiter_id = ?
            ORDER BY t.table_number ASC;
            """,
            (waiter_id,)
        )

    def get_all_tables_with_waiters(self) -> List[Dict]:
        """Returns all tables with assigned waiter names and live occupancy for Manager overview."""
        return self.db.fetchall(
            """
            SELECT t.id, t.table_number, t.zone, t.capacity, t.status, t.active_order_id,
                   t.waiter_id, u.full_name as waiter_name, u.username as waiter_username,
                   o.order_number, o.status as order_status, o.customer_name as active_customer_name,
                   (SELECT COUNT(*) FROM service_requests sr WHERE sr.table_number = t.table_number AND sr.status IN ('PENDING', 'IN_PROGRESS')) as pending_requests_count
            FROM restaurant_tables t
            LEFT JOIN users u ON t.waiter_id = u.id
            LEFT JOIN orders o ON t.active_order_id = o.id
            ORDER BY t.table_number ASC;
            """
        )

    def assign_table_to_waiter(self, table_number: str, waiter_id: Optional[int]) -> Tuple[bool, str]:
        """Assigns or clears a waiter assignment for a specific table, validating waiter active status."""
        if waiter_id is not None:
            waiter_user = self.user_repo.get_by_id(waiter_id)
            if not waiter_user:
                return False, "Selected waiter user not found."
            if not waiter_user.is_active:
                return False, f"Cannot assign table to inactive account '{waiter_user.username}'."
            if not waiter_user.is_waiter():
                return False, f"User '{waiter_user.username}' does not hold the WAITER role."

        try:
            self.db.execute(
                "UPDATE restaurant_tables SET waiter_id = ?, updated_at = CURRENT_TIMESTAMP WHERE table_number = ?;",
                (waiter_id, table_number)
            )
            # If table has an active order, also associate this waiter
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

    def get_ready_orders(self, waiter_id: Optional[int] = None) -> List[Dict]:
        """Returns orders currently marked READY at the kitchen pass waiting for pickup.
        
        If waiter_id is specified: returns orders assigned to this waiter PLUS unassigned orders.
        """
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.created_at, o.updated_at,
                   u.full_name as waiter_name,
                   (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 as elapsed_ready_mins
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status = 'READY'
        """
        params = []
        if waiter_id is not None:
            sql += " AND (o.waiter_id = ? OR o.waiter_id IS NULL)"
            params.append(waiter_id)
        sql += " ORDER BY o.updated_at ASC;"
        return self.db.fetchall(sql, tuple(params))

    def get_unassigned_ready_orders(self) -> List[Dict]:
        """Returns ready orders that have no waiter assigned yet."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.created_at, o.updated_at,
                   (julianday('now', 'localtime') - julianday(o.updated_at)) * 24 * 60 as elapsed_ready_mins
            FROM orders o
            WHERE o.status = 'READY' AND o.waiter_id IS NULL
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
                   u.full_name as waiter_name,
                   (julianday(o.served_at) - julianday(o.picked_up_at)) * 24 * 60 as serving_duration_mins
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

    def get_serving_history(
        self,
        waiter_id: Optional[int] = None,
        search_query: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Returns completed serving history (SERVED and COMPLETED) with durations and search filtering."""
        sql = """
            SELECT o.id, o.order_number, o.table_number, o.customer_name, o.status,
                   o.special_instructions, o.waiter_id, o.served_at, o.picked_up_at, o.created_at,
                   u.full_name as waiter_name,
                   ROUND((julianday(COALESCE(o.served_at, o.updated_at)) - julianday(COALESCE(o.picked_up_at, o.created_at))) * 24 * 60, 1) as serving_duration_mins
            FROM orders o
            LEFT JOIN users u ON o.waiter_id = u.id
            WHERE o.status IN ('SERVED', 'COMPLETED')
        """
        params = []
        if waiter_id is not None:
            sql += " AND o.waiter_id = ?"
            params.append(waiter_id)
        if search_query:
            term = f"%{search_query.strip()}%"
            sql += " AND (o.order_number LIKE ? OR o.table_number LIKE ? OR o.customer_name LIKE ?)"
            params.extend([term, term, term])

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

    # ── Customer Service Requests (Assistance Flow) ───────────────────────

    def create_service_request(
        self,
        table_number: str,
        request_type: str,
        notes: str = "",
        order_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        customer_name: str = "Guest"
    ) -> Tuple[bool, str, Optional[int]]:
        """Customer raises an on-table service request (Water, Cutlery, Napkins, Assistance)."""
        valid_types = {"Water", "Extra Cutlery", "Napkins", "Additional Assistance", "Other Customer Request"}
        # If not exact match, normalize
        matched_type = request_type
        if request_type not in valid_types:
            for vt in valid_types:
                if request_type.lower() in vt.lower():
                    matched_type = vt
                    break

        try:
            # Find waiter assigned to this table if any
            table_row = self.db.fetchone(
                "SELECT waiter_id FROM restaurant_tables WHERE table_number = ?;",
                (table_number,)
            )
            assigned_waiter = table_row["waiter_id"] if (table_row and "waiter_id" in table_row.keys()) else None

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO service_requests (table_number, order_id, customer_id, customer_name, request_type, notes, status, assigned_waiter_id)
                    VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?);
                    """,
                    (table_number, order_id, customer_id, customer_name, matched_type, notes.strip(), assigned_waiter)
                )
                req_id = cursor.lastrowid

                # Audit trail
                cursor.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES (?, 'REQUEST_CREATED', 'SERVICE', ?);",
                    (customer_name, f"Customer at {table_number} requested {matched_type} (Req #{req_id})")
                )

            logger.info(f"Service request #{req_id} ({matched_type}) created for table {table_number}.")
            return True, f"Request for '{matched_type}' sent to your floor server.", req_id
        except Exception as e:
            logger.error(f"Error creating service request: {e}")
            return False, str(e), None

    def get_service_requests(
        self,
        waiter_id: Optional[int] = None,
        status: Optional[str] = None,
        table_number: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Returns customer service requests filtered by waiter, status, or table."""
        sql = """
            SELECT sr.id, sr.table_number, sr.order_id, sr.customer_id, sr.customer_name,
                   sr.request_type, sr.notes, sr.status, sr.assigned_waiter_id,
                   sr.created_at, sr.resolved_at,
                   u.full_name as waiter_name,
                   (julianday('now', 'localtime') - julianday(sr.created_at)) * 24 * 60 as elapsed_mins
            FROM service_requests sr
            LEFT JOIN users u ON sr.assigned_waiter_id = u.id
            WHERE 1=1
        """
        params = []
        if waiter_id is not None:
            sql += " AND (sr.assigned_waiter_id = ? OR sr.assigned_waiter_id IS NULL)"
            params.append(waiter_id)
        if status:
            sql += " AND sr.status = ?"
            params.append(status)
        if table_number:
            sql += " AND sr.table_number = ?"
            params.append(table_number)

        sql += " ORDER BY sr.id DESC LIMIT ?;"
        params.append(limit)
        return self.db.fetchall(sql, tuple(params))

    def accept_service_request(self, request_id: int, waiter_id: int) -> Tuple[bool, str]:
        """Marks a service request as IN_PROGRESS by waiter."""
        try:
            waiter_user = self.user_repo.get_by_id(waiter_id)
            waiter_name = waiter_user.full_name if waiter_user else f"Server #{waiter_id}"

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE service_requests SET status = 'IN_PROGRESS', assigned_waiter_id = ? WHERE id = ?;",
                    (waiter_id, request_id)
                )
                cursor.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES (?, 'REQUEST_ACCEPTED', 'SERVICE', ?);",
                    (waiter_name, f"Accepted customer request #{request_id}")
                )
            logger.info(f"Service request #{request_id} accepted by waiter {waiter_id}.")
            return True, f"Request #{request_id} marked as In Progress."
        except Exception as e:
            logger.error(f"Error accepting service request: {e}")
            return False, str(e)

    def resolve_service_request(self, request_id: int, waiter_id: int) -> Tuple[bool, str]:
        """Marks a service request as RESOLVED."""
        try:
            waiter_user = self.user_repo.get_by_id(waiter_id)
            waiter_name = waiter_user.full_name if waiter_user else f"Server #{waiter_id}"

            with self.db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE service_requests SET status = 'RESOLVED', assigned_waiter_id = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (waiter_id, request_id)
                )
                cursor.execute(
                    "INSERT INTO audit_logs (username, action, module, details) VALUES (?, 'REQUEST_RESOLVED', 'SERVICE', ?);",
                    (waiter_name, f"Resolved customer request #{request_id}")
                )
            logger.info(f"Service request #{request_id} resolved by waiter {waiter_id}.")
            return True, f"Request #{request_id} resolved successfully."
        except Exception as e:
            logger.error(f"Error resolving service request: {e}")
            return False, str(e)

    def get_pending_requests_count(self, waiter_id: Optional[int] = None) -> int:
        """Returns count of active requests waiting for resolution."""
        if waiter_id is not None:
            row = self.db.fetchone(
                "SELECT COUNT(*) FROM service_requests WHERE status IN ('PENDING', 'IN_PROGRESS') AND (assigned_waiter_id = ? OR assigned_waiter_id IS NULL);",
                (waiter_id,)
            )
        else:
            row = self.db.fetchone("SELECT COUNT(*) FROM service_requests WHERE status IN ('PENDING', 'IN_PROGRESS');")
        return row[0] if row else 0

    def get_waiter_telemetry(self, waiter_id: Optional[int] = None) -> Dict[str, int]:
        """Returns KPI counts for waiter operational dashboard."""
        ready_cnt = len(self.get_ready_orders(waiter_id=waiter_id))
        picked_up_cnt = len(self.get_picked_up_orders(waiter_id=waiter_id))
        served_cnt = len(self.get_served_orders(waiter_id=waiter_id, limit=200))
        tables_cnt = len(self.get_assigned_tables(waiter_id)) if waiter_id else 0
        requests_cnt = self.get_pending_requests_count(waiter_id=waiter_id)
        return {
            "ready_count": ready_cnt,
            "transit_count": picked_up_cnt,
            "served_count": served_cnt,
            "tables_count": tables_cnt,
            "requests_count": requests_cnt
        }

    def get_waiter_workload_summary(self) -> List[Dict]:
        """Returns workload metrics across all active waiters for Manager oversight."""
        waiters = self.get_all_waiters(active_only=False)
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        summary = []
        for w in waiters:
            assigned_tables = len(self.get_assigned_tables(w.id))
            in_transit = len(self.get_picked_up_orders(waiter_id=w.id))
            served_today = self.db.fetchone(
                "SELECT COUNT(*) FROM orders WHERE waiter_id = ? AND status IN ('SERVED', 'COMPLETED') AND served_at LIKE ?;",
                (w.id, f"{today_prefix}%")
            )[0]
            open_requests = self.get_pending_requests_count(waiter_id=w.id)
            summary.append({
                "waiter_id": w.id,
                "username": w.username,
                "full_name": w.full_name,
                "is_active": w.is_active,
                "assigned_tables": assigned_tables,
                "in_transit": in_transit,
                "served_today": served_today,
                "open_requests": open_requests
            })
        return summary


# Global instance
waiter_service = WaiterService()
