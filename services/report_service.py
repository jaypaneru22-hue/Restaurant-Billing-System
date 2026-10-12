"""Report service aggregating historical analytics and rendering Matplotlib figures (Q08-F2)."""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for GUI embedding & headless testing
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from database.db import DatabaseManager, db
from config.settings import THEME_PALETTES
from utils.logger import logger


class ReportService:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_sales_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Returns daily sales totals for the last N days."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        rows = self.db.fetchall(
            """SELECT DATE(b.billed_at) as sale_date,
                      COUNT(b.id) as order_count,
                      COALESCE(SUM(b.final_total), 0) as total_sales
               FROM bills b
               WHERE DATE(b.billed_at) >= DATE(?) AND DATE(b.billed_at) <= DATE(?)
               GROUP BY DATE(b.billed_at)
               ORDER BY sale_date ASC;""",
            (start_date.isoformat(), end_date.isoformat())
        )
        sales_map = {r["sale_date"]: (Decimal(str(r["total_sales"])), int(r["order_count"])) for r in rows}

        results = []
        for i in range(days):
            current = start_date + timedelta(days=i)
            cur_str = current.isoformat()
            total, count = sales_map.get(cur_str, (Decimal("0.00"), 0))
            results.append({
                "date": cur_str,
                "label": current.strftime("%d %b"),
                "total_sales": total.quantize(Decimal("0.01")),
                "order_count": count
            })
        return results

    def get_top_selling_items(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Returns top menu items by volume sold."""
        rows = self.db.fetchall(
            """SELECT oi.item_name, SUM(oi.quantity) as total_qty, SUM(oi.line_total) as total_revenue
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               WHERE o.status = 'COMPLETED'
               GROUP BY oi.item_name
               ORDER BY total_qty DESC LIMIT ?;""",
            (limit,)
        )
        return [
            {
                "item_name": r["item_name"],
                "quantity": int(r["total_qty"]),
                "revenue": Decimal(str(r["total_revenue"])).quantize(Decimal("0.01"))
            }
            for r in rows
        ]

    def get_order_status_distribution(self) -> Dict[str, int]:
        """Returns counts for PENDING, COMPLETED, CANCELLED orders."""
        rows = self.db.fetchall(
            "SELECT status, COUNT(*) as count FROM orders GROUP BY status;"
        )
        status_map = {"COMPLETED": 0, "PENDING": 0, "CANCELLED": 0}
        for r in rows:
            st = r["status"].upper()
            if st in status_map:
                status_map[st] = int(r["count"])
        return status_map

    def get_payment_method_distribution(self) -> Dict[str, int]:
        """Returns counts for CASH, CARD, UPI payments."""
        rows = self.db.fetchall(
            "SELECT payment_method, COUNT(*) as count FROM bills GROUP BY payment_method;"
        )
        pay_map = {"CASH": 0, "CARD": 0, "UPI": 0}
        for r in rows:
            pm = r["payment_method"].upper()
            if pm in pay_map:
                pay_map[pm] = int(r["count"])
        return pay_map

    def _setup_figure_style(self, fig: Figure, ax, theme: str = "dark"):
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
        bg_card = palette["bg_card"]
        text_primary = palette["text_primary"]
        text_secondary = palette["text_secondary"]
        border = palette["border"]

        fig.patch.set_facecolor(bg_card)
        ax.set_facecolor(bg_card)
        ax.tick_params(colors=text_secondary, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(border)
        ax.xaxis.label.set_color(text_primary)
        ax.yaxis.label.set_color(text_primary)
        ax.title.set_color(text_primary)

    def plot_daily_sales(self, theme: str = "dark", days: int = 7) -> Figure:
        """Renders Daily Sales Trend bar chart."""
        data = self.get_sales_trend(days)
        labels = [d["label"] for d in data]
        values = [float(d["total_sales"]) for d in data]

        palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
        fig = Figure(figsize=(5.5, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        self._setup_figure_style(fig, ax, theme)

        bars = ax.bar(labels, values, color=palette["accent"], width=0.55, edgecolor=palette["border"])
        ax.set_title(f"Sales Revenue — Last {days} Days (₹)", fontsize=11, fontweight="bold", pad=10)
        ax.grid(axis="y", linestyle="--", alpha=0.25, color=palette["border"])

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"₹{int(height)}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center", va="bottom",
                    fontsize=8,
                    color=palette["text_primary"]
                )

        fig.tight_layout()
        return fig

    def plot_top_items(self, theme: str = "dark", limit: int = 6) -> Figure:
        """Renders Best-Selling Menu Items horizontal bar chart."""
        data = self.get_top_selling_items(limit)
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
        fig = Figure(figsize=(5.5, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        self._setup_figure_style(fig, ax, theme)

        if not data:
            ax.text(0.5, 0.5, "No sales recorded yet", ha="center", va="center", color=palette["text_secondary"], fontsize=11)
            ax.set_title("Best-Selling Menu Items", fontsize=11, fontweight="bold", pad=10)
            fig.tight_layout()
            return fig

        # Invert so highest is on top
        names = [d["item_name"][:18] for d in reversed(data)]
        counts = [d["quantity"] for d in reversed(data)]

        bars = ax.barh(names, counts, color=palette["success"], height=0.55, edgecolor=palette["border"])
        ax.set_title("Top Menu Items by Volume Sold", fontsize=11, fontweight="bold", pad=10)
        ax.grid(axis="x", linestyle="--", alpha=0.25, color=palette["border"])

        for bar in bars:
            width = bar.get_width()
            ax.annotate(
                f"{int(width)} pcs",
                xy=(width, bar.get_y() + bar.get_height() / 2),
                xytext=(5, 0),
                textcoords="offset points",
                ha="left", va="center",
                fontsize=8,
                color=palette["text_primary"]
            )

        fig.tight_layout()
        return fig

    def plot_order_status(self, theme: str = "dark") -> Figure:
        """Renders Order Status Distribution pie/donut chart."""
        data = self.get_order_status_distribution()
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
        fig = Figure(figsize=(5.5, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        self._setup_figure_style(fig, ax, theme)

        total_orders = sum(data.values())
        if total_orders == 0:
            ax.text(0.5, 0.5, "No orders available", ha="center", va="center", color=palette["text_secondary"], fontsize=11)
            ax.set_title("Order Status Distribution", fontsize=11, fontweight="bold", pad=10)
            fig.tight_layout()
            return fig

        labels = []
        sizes = []
        colors = []
        color_map = {
            "COMPLETED": palette["success"],
            "PENDING": palette["warning"],
            "CANCELLED": palette["danger"]
        }
        for st, count in data.items():
            if count > 0:
                labels.append(f"{st} ({count})")
                sizes.append(count)
                colors.append(color_map.get(st, palette["accent"]))

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct="%1.0f%%",
            startangle=140,
            wedgeprops={"edgecolor": palette["bg_card"], "linewidth": 1.5}
        )
        for t in texts:
            t.set_color(palette["text_primary"])
            t.set_fontsize(8)
        for at in autotexts:
            at.set_color("#ffffff")
            at.set_fontsize(9)
            at.set_fontweight("bold")

        ax.set_title("Order Status Breakdown", fontsize=11, fontweight="bold", pad=10)
        fig.tight_layout()
        return fig

    def plot_payment_methods(self, theme: str = "dark") -> Figure:
        """Renders Payment Method Distribution pie/donut chart."""
        data = self.get_payment_method_distribution()
        palette = THEME_PALETTES.get(theme, THEME_PALETTES["dark"])
        fig = Figure(figsize=(5.5, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        self._setup_figure_style(fig, ax, theme)

        total_payments = sum(data.values())
        if total_payments == 0:
            ax.text(0.5, 0.5, "No completed payments yet", ha="center", va="center", color=palette["text_secondary"], fontsize=11)
            ax.set_title("Payment Method Distribution", fontsize=11, fontweight="bold", pad=10)
            fig.tight_layout()
            return fig

        labels = []
        sizes = []
        colors = [palette["accent"], palette["success"], palette["warning"]]
        idx = 0
        assigned_colors = []
        for method, count in data.items():
            if count > 0:
                labels.append(f"{method} ({count})")
                sizes.append(count)
                assigned_colors.append(colors[idx % len(colors)])
                idx += 1

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=assigned_colors,
            autopct="%1.0f%%",
            startangle=90,
            wedgeprops={"edgecolor": palette["bg_card"], "linewidth": 1.5}
        )
        for t in texts:
            t.set_color(palette["text_primary"])
            t.set_fontsize(8)
        for at in autotexts:
            at.set_color("#ffffff")
            at.set_fontsize(9)
            at.set_fontweight("bold")

        ax.set_title("Payment Methods Distribution", fontsize=11, fontweight="bold", pad=10)
        fig.tight_layout()
        return fig


# Global report service instance
report_service = ReportService()
