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


# Global dashboard service instance
dashboard_service = DashboardService()
