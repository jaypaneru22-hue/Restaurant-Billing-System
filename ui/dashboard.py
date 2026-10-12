"""Interactive Dashboard view displaying real-time database KPIs and quick actions (Q08-F1)."""
import customtkinter as ctk
from typing import Callable, Optional
from services.dashboard_service import DashboardService, dashboard_service
from ui.theme_manager import theme_manager
from config.settings import CURRENCY_SYMBOL


class DashboardFrame(ctk.CTkFrame):
    """Real-time operational dashboard with metric cards, recent orders, and top items."""

    def __init__(self, master, navigate_fn: Callable[[str], None], dashboard_svc: DashboardService = dashboard_service, **kwargs):
        super().__init__(master, **kwargs)
        self.navigate = navigate_fn
        self.dashboard_svc = dashboard_svc

        # Register theme listener
        theme_manager.subscribe(self.on_theme_changed)

        self._build_ui()
        self.refresh_data()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_data()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Top Header & Quick Actions Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="📊 Operational Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Real-time Point-of-Sale metrics & continuous quality monitoring",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Action Buttons
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        refresh_btn = ctk.CTkButton(
            actions_box,
            text="🔄 Refresh",
            width=90,
            height=34,
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_data
        )
        refresh_btn.pack(side="right", padx=5)

        new_ord_btn = ctk.CTkButton(
            actions_box,
            text="➕ New Order",
            width=110,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("orders")
        )
        new_ord_btn.pack(side="right", padx=5)

        # KPI Metric Cards Container (4 cards in a grid)
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=25, pady=(0, 20))
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        self.card_sales = self._create_metric_card(self.kpi_container, 0, "💰 Today's Sales", f"{CURRENCY_SYMBOL}0.00", palette["success"])
        self.card_completed = self._create_metric_card(self.kpi_container, 1, "🧾 Completed Orders", "0", palette["accent"])
        self.card_pending = self._create_metric_card(self.kpi_container, 2, "⏳ Pending Orders", "0", palette["warning"])
        self.card_aov = self._create_metric_card(self.kpi_container, 3, "📈 Avg Order Value", f"{CURRENCY_SYMBOL}0.00", palette["text_primary"])

        # Split Lower Section (Recent Orders & Top Items)
        content_split = ctk.CTkFrame(self, fg_color="transparent")
        content_split.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        content_split.grid_columnconfigure(0, weight=3, uniform="split")
        content_split.grid_columnconfigure(1, weight=2, uniform="split")
        content_split.grid_rowconfigure(0, weight=1)

        # Left Panel: Recent Orders
        self.recent_frame = ctk.CTkFrame(content_split, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.recent_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        recent_header = ctk.CTkFrame(self.recent_frame, fg_color="transparent")
        recent_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(
            recent_header,
            text="Recent Transactions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")
        ctk.CTkButton(
            recent_header,
            text="View All",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            command=lambda: self.navigate("orders_history")
        ).pack(side="right")

        self.recent_list_box = ctk.CTkScrollableFrame(self.recent_frame, fg_color="transparent")
        self.recent_list_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Right Panel: Popular Menu Items
        self.popular_frame = ctk.CTkFrame(content_split, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.popular_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        popular_header = ctk.CTkFrame(self.popular_frame, fg_color="transparent")
        popular_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(
            popular_header,
            text="🔥 Top Selling Dishes",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        self.popular_list_box = ctk.CTkScrollableFrame(self.popular_frame, fg_color="transparent")
        self.popular_list_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_metric_card(self, parent, col, title, initial_value, value_color):
        palette = theme_manager.get_palette()
        card = ctk.CTkFrame(parent, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        card.grid(row=0, column=col, sticky="ew", padx=6)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", padx=16, pady=(14, 4))

        val_lbl = ctk.CTkLabel(
            card,
            text=initial_value,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=value_color
        )
        val_lbl.pack(anchor="w", padx=16, pady=(0, 14))
        return val_lbl

    def refresh_data(self):
        """Fetches fresh metrics from database and updates GUI widgets."""
        metrics = self.dashboard_svc.get_dashboard_metrics()
        palette = theme_manager.get_palette()

        # Update KPI cards
        self.card_sales.configure(text=f"{CURRENCY_SYMBOL}{metrics['today_sales']}")
        self.card_completed.configure(text=str(metrics["completed_orders_count"]))
        self.card_pending.configure(text=str(metrics["pending_orders_count"]))
        self.card_aov.configure(text=f"{CURRENCY_SYMBOL}{metrics['average_order_value']}")

        # Clear and populate Recent Orders
        for child in self.recent_list_box.winfo_children():
            child.destroy()

        if not metrics["recent_orders"]:
            ctk.CTkLabel(
                self.recent_list_box,
                text="No orders recorded yet. Click '+ New Order' to begin.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"]
            ).pack(pady=30)
        else:
            for ord_data in metrics["recent_orders"]:
                item_row = ctk.CTkFrame(self.recent_list_box, fg_color=palette["bg_secondary"], corner_radius=8)
                item_row.pack(fill="x", pady=4, padx=2)

                info_box = ctk.CTkFrame(item_row, fg_color="transparent")
                info_box.pack(side="left", padx=12, pady=8)

                ctk.CTkLabel(
                    info_box,
                    text=f"{ord_data['order_number']}  •  {ord_data['customer_name']}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(anchor="w")

                ctk.CTkLabel(
                    info_box,
                    text=f"Table: {ord_data['table_number']}  |  {ord_data['created_at'] or ''}",
                    font=ctk.CTkFont(size=10),
                    text_color=palette["text_secondary"]
                ).pack(anchor="w")

                # Status pill & total
                status_color = palette["success"] if ord_data["status"] == "COMPLETED" else (
                    palette["warning"] if ord_data["status"] == "PENDING" else palette["danger"]
                )
                right_box = ctk.CTkFrame(item_row, fg_color="transparent")
                right_box.pack(side="right", padx=12, pady=8)

                ctk.CTkLabel(
                    right_box,
                    text=f"{CURRENCY_SYMBOL}{ord_data['total']}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(anchor="e")

                ctk.CTkLabel(
                    right_box,
                    text=ord_data["status"],
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=status_color
                ).pack(anchor="e")

        # Clear and populate Popular Items
        for child in self.popular_list_box.winfo_children():
            child.destroy()

        if not metrics["popular_items"]:
            ctk.CTkLabel(
                self.popular_list_box,
                text="No sales data available yet.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"]
            ).pack(pady=30)
        else:
            for rank, pop in enumerate(metrics["popular_items"], start=1):
                item_row = ctk.CTkFrame(self.popular_list_box, fg_color=palette["bg_secondary"], corner_radius=8)
                item_row.pack(fill="x", pady=4, padx=2)

                left = ctk.CTkFrame(item_row, fg_color="transparent")
                left.pack(side="left", padx=10, pady=8)

                ctk.CTkLabel(
                    left,
                    text=f"#{rank} {pop['name']}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=palette["text_primary"]
                ).pack(anchor="w")

                ctk.CTkLabel(
                    left,
                    text=f"Revenue: {CURRENCY_SYMBOL}{pop['revenue']}",
                    font=ctk.CTkFont(size=10),
                    text_color=palette["text_secondary"]
                ).pack(anchor="w")

                ctk.CTkLabel(
                    item_row,
                    text=f"{pop['quantity_sold']} sold",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=palette["accent"]
                ).pack(side="right", padx=12, pady=8)
