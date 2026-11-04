"""Dashboard service aggregating real-time operational KPIs from the database (Q08-F1)."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from database.db import DatabaseManager, db
from utils.logger import logger


class DashboardService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_dashboard_metrics(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculates live operational metrics from SQLite database queries."""
        date_str = target_date or datetime.now().strftime("%Y-%m-%d")

        # 1. Today's Total Sales and Completed Orders Count
        # bills.billed_at is TIMESTAMP formatted as YYYY-MM-DD HH:MM:SS or ISO
        sales_row = self.db.fetchone(
            """SELECT COUNT(b.id) AS completed_count,
                      COALESCE(SUM(b.final_total), 0) AS total_sales
               FROM bills b
               WHERE DATE(b.billed_at) = DATE(?);""",
            (date_str,)
        )
        completed_count = int(sales_row["completed_count"]) if sales_row else 0
        total_sales = Decimal(str(sales_row["total_sales"])) if sales_row else Decimal("0.00")

        # 2. Pending Orders Count (All active pending orders regardless of date)
        pending_row = self.db.fetchone(
            "SELECT COUNT(*) AS pending_count FROM orders WHERE status = 'PENDING';"
        )
        pending_count = int(pending_row["pending_count"]) if pending_row else 0

        # 3. Average Order Value (AOV)
        if completed_count > 0:
            aov = (total_sales / Decimal(completed_count)).quantize(Decimal("0.01"))
        else:
            aov = Decimal("0.00")

        # 4. Total orders created today (Pending + Completed + Cancelled)
        total_today_row = self.db.fetchone(
            "SELECT COUNT(*) AS total_today FROM orders WHERE DATE(created_at) = DATE(?);",
            (date_str,)
        )
        total_orders_today = int(total_today_row["total_today"]) if total_today_row else 0

        # 5. Recent Orders (Last 5 orders)
        recent_rows = self.db.fetchall(
            """SELECT o.id, o.order_number, o.customer_name, o.table_number, o.status,
                      o.created_at, COALESCE(b.final_total, 0) AS final_total
               FROM orders o
               LEFT JOIN bills b ON o.id = b.order_id
               ORDER BY o.id DESC LIMIT 5;"""
        )
        recent_orders = [
            {
                "id": r["id"],
                "order_number": r["order_number"],
                "customer_name": r["customer_name"],
                "table_number": r["table_number"],
                "status": r["status"],
                "created_at": r["created_at"],
                "total": Decimal(str(r["final_total"])).quantize(Decimal("0.01"))
            }
            for r in recent_rows
        ]

        # 6. Popular Menu Items (Top 5 items by total quantity sold)
        popular_rows = self.db.fetchall(
            """SELECT oi.item_name, SUM(oi.quantity) AS total_qty, SUM(oi.line_total) AS total_revenue
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               WHERE o.status = 'COMPLETED'
               GROUP BY oi.item_name
               ORDER BY total_qty DESC LIMIT 5;"""
        )
        popular_items = [
            {
                "name": r["item_name"],
                "quantity_sold": int(r["total_qty"]),
                "revenue": Decimal(str(r["total_revenue"])).quantize(Decimal("0.01"))
            }
            for r in popular_rows
        ]

        # 7. Menu item count
        menu_count_row = self.db.fetchone("SELECT COUNT(*) AS total_items FROM menu_items WHERE is_available = 1;")
        active_menu_count = int(menu_count_row["total_items"]) if menu_count_row else 0

        return {
            "date": date_str,
            "today_sales": total_sales.quantize(Decimal("0.01")),
            "completed_orders_count": completed_count,
            "pending_orders_count": pending_count,
            "total_orders_today": total_orders_today,
            "average_order_value": aov,
            "recent_orders": recent_orders,
            "popular_items": popular_items,
            "active_menu_items_count": active_menu_count
        }

    def get_admin_metrics(self) -> Dict[str, Any]:
        """Calculates executive-level restaurant management metrics directly from SQLite database."""
        # 1. Total Staff & Active Users
        staff_row = self.db.fetchone("SELECT COUNT(*) AS total_staff FROM users;")
        total_staff = int(staff_row["total_staff"]) if staff_row else 0
        active_row = self.db.fetchone("SELECT COUNT(*) AS active_users FROM users WHERE is_active = 1;")
        active_users = int(active_row["active_users"]) if active_row else 0

        # 2. Total Orders (All-time orders count)
        orders_row = self.db.fetchone("SELECT COUNT(*) AS total_orders FROM orders;")
        total_orders = int(orders_row["total_orders"]) if orders_row else 0

        # 3. Total Sales (All-time settled revenue) & Total Transactions (Paid bills count)
        all_time_row = self.db.fetchone(
            "SELECT COALESCE(SUM(final_total), 0) AS total_rev, COUNT(*) AS total_bills FROM bills WHERE payment_status = 'PAID';"
        )
        total_sales = Decimal(str(all_time_row["total_rev"])) if all_time_row else Decimal("0.00")
        total_transactions = int(all_time_row["total_bills"]) if all_time_row else 0

        # 4. Today's Gross Sales & Today's Orders
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_row = self.db.fetchone(
            "SELECT COALESCE(SUM(final_total), 0) AS today_rev, COUNT(*) AS today_count FROM bills WHERE payment_status = 'PAID' AND DATE(billed_at) = DATE(?);",
            (today_str,)
        )
        today_sales = Decimal(str(today_row["today_rev"])) if today_row else Decimal("0.00")
        today_orders = int(today_row["today_count"]) if today_row else 0

        # 5. Active Pending Orders
        pending_row = self.db.fetchone("SELECT COUNT(*) AS pending_count FROM orders WHERE status = 'PENDING';")
        pending_orders = int(pending_row["pending_count"]) if pending_row else 0

        # 6. System Status Check (Probe connection & foreign keys)
        try:
            probe = self.db.fetchone("SELECT 1;")
            system_status = "ONLINE • HEALTHY" if probe else "DEGRADED"
        except Exception:
            system_status = "ERROR"

        # 7. Active Catalog Health
        catalog_row = self.db.fetchone(
            "SELECT COUNT(*) AS total_dishes, SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) AS active_dishes FROM menu_items;"
        )
        total_dishes = int(catalog_row["total_dishes"]) if catalog_row else 0
        active_dishes = int(catalog_row["active_dishes"]) if catalog_row and catalog_row["active_dishes"] else 0

        # 8. Payment breakdown
        pay_rows = self.db.fetchall("SELECT payment_method, COALESCE(SUM(final_total), 0) as total FROM bills WHERE payment_status = 'PAID' GROUP BY payment_method;")
        payment_breakdown = {r["payment_method"]: Decimal(str(r["total"])).quantize(Decimal("0.01")) for r in pay_rows}

        # 9. Recent transactions with Cashier & Table
        recent_rows = self.db.fetchall(
            """SELECT o.order_number, o.customer_name, o.table_number, o.status,
                      COALESCE(u.full_name, 'Staff') AS staff_name,
                      COALESCE(b.final_total, 0) AS final_total,
                      COALESCE(b.payment_method, '-') AS payment_method,
                      o.created_at
               FROM orders o
               LEFT JOIN users u ON o.user_id = u.id
               LEFT JOIN bills b ON o.id = b.order_id
               ORDER BY o.id DESC LIMIT 6;"""
        )
        recent_txns = [
            {
                "order_number": r["order_number"],
                "customer": r["customer_name"],
                "table": r["table_number"],
                "status": r["status"],
                "staff": r["staff_name"],
                "amount": Decimal(str(r["final_total"])).quantize(Decimal("0.01")),
                "payment_method": r["payment_method"],
                "created_at": r["created_at"]
            }
            for r in recent_rows
        ]

        # 10. Average Order Value
        aov = (total_sales / Decimal(total_transactions)).quantize(Decimal("0.01")) if total_transactions > 0 else Decimal("0.00")

        return {
            # Required 7 KPIs
            "total_staff": total_staff,
            "active_users": active_users,
            "total_orders": total_orders,
            "total_sales": total_sales.quantize(Decimal("0.01")),
            "total_transactions": total_transactions,
            "pending_orders": pending_orders,
            "system_status": system_status,

            # Backwards compatibility & chart helpers
            "total_revenue": total_sales.quantize(Decimal("0.01")),
            "total_bills": total_transactions,
            "pending_count": pending_orders,
            "today_sales": today_sales.quantize(Decimal("0.01")),
            "today_orders": today_orders,
            "active_dishes": active_dishes,
            "total_dishes": total_dishes,
            "average_order_value": aov,
            "payment_breakdown": payment_breakdown,
            "recent_transactions": recent_txns
        }

    def get_cashier_metrics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculates shift and billing-focused metrics for front-counter cashiers."""
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 1. My shift completed tickets & sales today
        sales_row = self.db.fetchone(
            """SELECT COUNT(b.id) AS my_count, COALESCE(SUM(b.final_total), 0) AS my_sales
               FROM bills b
               WHERE DATE(b.billed_at) = DATE(?);""",
            (today_str,)
        )

        shift_sales = Decimal(str(sales_row["my_sales"])) if sales_row else Decimal("0.00")
        shift_tickets = int(sales_row["my_count"]) if sales_row else 0

        # 2. Active Pending counter & customer tickets awaiting cashier billing
        pending_row = self.db.fetchone(
            """SELECT COUNT(o.id) AS pending_count
               FROM orders o
               LEFT JOIN bills b ON o.id = b.order_id
               WHERE b.id IS NULL AND o.status != 'CANCELLED';"""
        )
        pending_count = int(pending_row["pending_count"]) if pending_row else 0

        # 3. Recent tickets created by / assigned to this terminal (prioritizing unbilled served orders)
        recent_rows = self.db.fetchall(
            """SELECT o.id, o.order_number, o.customer_name, o.table_number, o.status,
                      COALESCE(b.final_total, (SELECT SUM(line_total) FROM order_items WHERE order_id = o.id), 0) AS final_total,
                      COALESCE(b.payment_method, 'UNBILLED') AS payment_method,
                      b.id AS bill_id,
                      o.created_at,
                      o.picked_up_at,
                      o.served_at
               FROM orders o
               LEFT JOIN bills b ON o.id = b.order_id
               WHERE o.status != 'CANCELLED'
               ORDER BY 
                   CASE 
                       WHEN b.id IS NULL AND (o.status = 'SERVED' OR o.served_at IS NOT NULL) THEN 1
                       WHEN b.id IS NULL AND o.status = 'READY' THEN 2
                       WHEN b.id IS NULL THEN 3
                       ELSE 4
                   END ASC,
                   o.id DESC LIMIT 10;"""
        )
        recent_tickets = [
            {
                "id": r["id"],
                "order_number": r["order_number"],
                "customer": r["customer_name"],
                "table": r["table_number"],
                "status": r["status"],
                "total": Decimal(str(r["final_total"])).quantize(Decimal("0.01")),
                "payment_method": r["payment_method"],
                "bill_id": r["bill_id"],
                "is_unbilled": (r["bill_id"] is None),
                "created_at": r["created_at"]
            }
            for r in recent_rows
        ]

        return {
            "shift_sales": shift_sales.quantize(Decimal("0.01")),
            "shift_tickets": shift_tickets,
            "pending_count": pending_count,
            "terminal_status": "Online • Ready for Billing",
            "recent_tickets": recent_tickets
        }

    def get_manager_metrics(self) -> Dict[str, Any]:
        """Calculates floor operations and catalog oversight metrics for Shift Managers."""
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 1. Floor Revenue Today
        today_row = self.db.fetchone(
            "SELECT COALESCE(SUM(final_total), 0) AS today_rev, COUNT(*) AS today_count FROM bills WHERE DATE(billed_at) = DATE(?);",
            (today_str,)
        )
        floor_revenue = Decimal(str(today_row["today_rev"])) if today_row else Decimal("0.00")
        orders_today = int(today_row["today_count"]) if today_row else 0

        # 2. Active Pending Tickets
        pending_row = self.db.fetchone("SELECT COUNT(*) AS pending_count FROM orders WHERE status = 'PENDING';")
        pending_count = int(pending_row["pending_count"]) if pending_row else 0

        # 3. Out-of-Stock Dishes (The 86 List)
        oos_row = self.db.fetchone("SELECT COUNT(*) AS oos_count FROM menu_items WHERE is_available = 0;")
        oos_count = int(oos_row["oos_count"]) if oos_row else 0

        # 4. Total Menu Items
        total_items_row = self.db.fetchone("SELECT COUNT(*) AS total_count FROM menu_items;")
        total_items = int(total_items_row["total_count"]) if total_items_row else 0

        # 5. Active Tables & Pending Orders queue
        pending_rows = self.db.fetchall(
            """SELECT o.id, o.order_number, o.customer_name, o.table_number, o.status, o.created_at,
                      COALESCE(SUM(oi.quantity), 0) AS item_count
               FROM orders o
               LEFT JOIN order_items oi ON o.id = oi.order_id
               WHERE o.status = 'PENDING'
               GROUP BY o.id
               ORDER BY o.id ASC LIMIT 5;"""
        )
        pending_orders = [
            {
                "id": r["id"],
                "order_number": r["order_number"],
                "customer": r["customer_name"],
                "table": r["table_number"],
                "items": int(r["item_count"]),
                "created_at": r["created_at"]
            }
            for r in pending_rows
        ]

        return {
            "floor_revenue": floor_revenue.quantize(Decimal("0.01")),
            "orders_today": orders_today,
            "pending_count": pending_count,
            "oos_count": oos_count,
            "total_items": total_items,
            "pending_orders": pending_orders
        }


# Global dashboard service instance
dashboard_service = DashboardService()
