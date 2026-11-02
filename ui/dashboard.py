"""Role-specific interactive dashboards for Admin, Cashier, and Manager personas."""
from typing import Callable, Optional, Dict, Any
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.dashboard_service import DashboardService, dashboard_service
from services.auth_service import AuthService, auth_service
from services.report_service import report_service
from ui.theme_manager import theme_manager
from config.settings import CURRENCY_SYMBOL


class DashboardFrame(ctk.CTkFrame):
    """Container that dynamically mounts the distinct dashboard tailored to the authenticated user's role."""

    def __init__(
        self,
        master,
        navigate_fn: Callable[[str], None],
        dashboard_svc: DashboardService = dashboard_service,
        auth_svc: AuthService = auth_service,
        role: Optional[str] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.navigate = navigate_fn
        self.dashboard_svc = dashboard_svc
        self.auth_svc = auth_svc

        # Resolve role
        if role:
            self.role = role.upper()
        elif self.auth_svc.current_user:
            self.role = self.auth_svc.current_user.role.upper()
        else:
            self.role = "ADMIN"

        # Matplotlib chart tracking
        self.left_chart_type = "daily"
        self.right_chart_type = "payment"
        self.fig_left = None
        self.fig_right = None
        self.chart_left_canvas = None
        self.chart_right_canvas = None

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_data()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        self._cleanup_charts()
        super().destroy()

    def _cleanup_left_chart(self):
        if hasattr(self, "chart_left_canvas") and self.chart_left_canvas:
            try:
                self.chart_left_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.chart_left_canvas = None
        if hasattr(self, "fig_left") and self.fig_left:
            try:
                plt.close(self.fig_left)
            except Exception:
                pass
            self.fig_left = None

    def _cleanup_right_chart(self):
        if hasattr(self, "chart_right_canvas") and self.chart_right_canvas:
            try:
                self.chart_right_canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self.chart_right_canvas = None
        if hasattr(self, "fig_right") and self.fig_right:
            try:
                plt.close(self.fig_right)
            except Exception:
                pass
            self.fig_right = None

    def _cleanup_charts(self):
        self._cleanup_left_chart()
        self._cleanup_right_chart()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_data()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Mount the specific role view
        if self.role == "CASHIER":
            self._build_cashier_dashboard(palette)
        elif self.role == "MANAGER":
            self._build_manager_dashboard(palette)
        elif self.role == "CHEF":
            self._build_chef_dashboard(palette)
        elif self.role == "CUSTOMER":
            self._build_customer_dashboard(palette)
        else:
            self._build_admin_dashboard(palette)

    # =========================================================================
    # 1. ADMIN DASHBOARD — COMPLETE EXECUTIVE CONTROL & LIVE TELEMETRY
    # =========================================================================
    def _build_admin_dashboard(self, palette: dict):
        self.admin_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.admin_scroll.pack(fill="both", expand=True)

        # Header Bar
        header = ctk.CTkFrame(self.admin_scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="🛡️ Admin Operations & Executive Governance",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Centralized enterprise management • Real-time database telemetry, live sales velocity and audit oversight",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Action bar
        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="🔄 Refresh Live Data",
            width=130,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_data
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            actions_box,
            text="📈 Full Analytics",
            width=110,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            command=lambda: self.navigate("reports")
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            actions_box,
            text="➕ New POS Order",
            width=135,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("orders")
        ).pack(side="left", padx=3)

        # ---------------------------------------------------------------------
        # 7 Executive KPI Cards Grid (2 Rows)
        # ---------------------------------------------------------------------
        kpi_grid = ctk.CTkFrame(self.admin_scroll, fg_color="transparent")
        kpi_grid.pack(fill="x", padx=24, pady=(0, 14))
        kpi_grid.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_admin")

        # Row 0: Total Staff, Active Users, Total Orders, Total Sales
        self.lbl_admin_staff, self.sub_admin_staff = self._create_kpi_card(
            kpi_grid, 0, "👥 Total Staff", "0", "Registered staff accounts", "#3B82F6", palette, row=0, pady=(0, 8)
        )
        self.lbl_admin_active_users, self.sub_admin_active_users = self._create_kpi_card(
            kpi_grid, 1, "🟢 Active Users", "0", "Active system accounts", "#10B981", palette, row=0, pady=(0, 8)
        )
        self.lbl_admin_total_orders, self.sub_admin_total_orders = self._create_kpi_card(
            kpi_grid, 2, "📦 Total Orders", "0", "All-time orders placed", "#8B5CF6", palette, row=0, pady=(0, 8)
        )
        self.lbl_admin_total_sales, self.sub_admin_total_sales = self._create_kpi_card(
            kpi_grid, 3, "💰 Total Sales", f"{CURRENCY_SYMBOL}0.00", "Gross settled revenue", "#059669", palette, row=0, pady=(0, 8)
        )

        # Row 1: Total Transactions, Pending Orders, System Status (columnspan=2)
        self.lbl_admin_txns, self.sub_admin_txns = self._create_kpi_card(
            kpi_grid, 0, "🧾 Total Transactions", "0", "Finalized paid bills", "#0284C7", palette, row=1
        )
        self.lbl_admin_pending, self.sub_admin_pending = self._create_kpi_card(
            kpi_grid, 1, "⏳ Pending Orders", "0", "Orders awaiting cashier billing", "#F59E0B", palette, row=1
        )
        self.lbl_admin_sys_status, self.sub_admin_sys_status = self._create_kpi_card(
            kpi_grid, 2, "⚡ System Status", "ONLINE • HEALTHY", "SQLite WAL • Real-time DB engine", "#10B981", palette, row=1, columnspan=2
        )

        # For backwards compatibility with any existing reference:
        self.lbl_admin_rev = self.lbl_admin_total_sales
        self.sub_admin_rev = self.sub_admin_total_sales
        self.lbl_admin_today = self.lbl_admin_total_sales
        self.sub_admin_today = self.sub_admin_total_sales
        self.lbl_admin_catalog = self.lbl_admin_total_orders
        self.sub_admin_catalog = self.sub_admin_total_orders

        # ---------------------------------------------------------------------
        # Live Visual Analytics Charts Section (2 Columns)
        # ---------------------------------------------------------------------
        charts_box = ctk.CTkFrame(self.admin_scroll, fg_color="transparent")
        charts_box.pack(fill="x", padx=24, pady=(0, 16))
        charts_box.grid_columnconfigure((0, 1), weight=1, uniform="admin_charts")

        # Left Chart Container: Sales Trend (Daily vs Monthly)
        chart_card_left = ctk.CTkFrame(charts_box, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        chart_card_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        c_head_left = ctk.CTkFrame(chart_card_left, fg_color="transparent")
        c_head_left.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(
            c_head_left,
            text="📈 Sales Revenue Velocity",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        toggles_left = ctk.CTkFrame(c_head_left, fg_color="transparent")
        toggles_left.pack(side="right")

        self.btn_chart_daily = ctk.CTkButton(
            toggles_left,
            text="Daily (7d)",
            width=70,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.set_left_chart("daily")
        )
        self.btn_chart_daily.pack(side="left", padx=2)

        self.btn_chart_monthly = ctk.CTkButton(
            toggles_left,
            text="Monthly (6m)",
            width=80,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=lambda: self.set_left_chart("monthly")
        )
        self.btn_chart_monthly.pack(side="left", padx=2)

        self.chart_left_container = ctk.CTkFrame(chart_card_left, fg_color="transparent", height=240)
        self.chart_left_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Right Chart Container: Distribution / Analytics (Payment vs Order Status vs Staff)
        chart_card_right = ctk.CTkFrame(charts_box, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        chart_card_right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        c_head_right = ctk.CTkFrame(chart_card_right, fg_color="transparent")
        c_head_right.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(
            c_head_right,
            text="📊 Operational Distribution",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        toggles_right = ctk.CTkFrame(c_head_right, fg_color="transparent")
        toggles_right.pack(side="right")

        self.btn_chart_pay = ctk.CTkButton(
            toggles_right,
            text="Payments",
            width=68,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.set_right_chart("payment")
        )
        self.btn_chart_pay.pack(side="left", padx=2)

        self.btn_chart_orders = ctk.CTkButton(
            toggles_right,
            text="Orders",
            width=58,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=lambda: self.set_right_chart("orders")
        )
        self.btn_chart_orders.pack(side="left", padx=2)

        self.btn_chart_staff = ctk.CTkButton(
            toggles_right,
            text="Staff Activity",
            width=80,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=lambda: self.set_right_chart("staff")
        )
        self.btn_chart_staff.pack(side="left", padx=2)

        self.chart_right_container = ctk.CTkFrame(chart_card_right, fg_color="transparent", height=240)
        self.chart_right_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ---------------------------------------------------------------------
        # Split Lower Grid: Left (Transactions 60%), Right (Channel breakdown & Actions 40%)
        # ---------------------------------------------------------------------
        grid_split = ctk.CTkFrame(self.admin_scroll, fg_color="transparent")
        grid_split.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        grid_split.grid_columnconfigure(0, weight=3, uniform="admin_split")
        grid_split.grid_columnconfigure(1, weight=2, uniform="admin_split")

        # Left Column: Recent Transactions Table
        card_txns = ctk.CTkFrame(grid_split, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_txns.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        head_txns = ctk.CTkFrame(card_txns, fg_color="transparent")
        head_txns.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            head_txns,
            text="Recent Restaurant Transactions (Audit Trail)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        ctk.CTkButton(
            head_txns,
            text="View Full Orders →",
            width=120,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            command=lambda: self.navigate("orders_history")
        ).pack(side="right")

        self.admin_txn_scroll = ctk.CTkScrollableFrame(card_txns, fg_color="transparent", height=220)
        self.admin_txn_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right Column: Payment Channels & Admin Shortcuts
        right_col = ctk.CTkFrame(grid_split, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Channel Breakdown
        card_channels = ctk.CTkFrame(right_col, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_channels.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card_channels,
            text="Settlement Breakdown by Channel",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=14, pady=(12, 8))

        self.box_channels = ctk.CTkFrame(card_channels, fg_color="transparent")
        self.box_channels.pack(fill="x", padx=14, pady=(0, 12))

        # Executive Quick Actions Card
        card_actions = ctk.CTkFrame(right_col, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_actions.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card_actions,
            text="Executive Quick Actions",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=14, pady=(12, 8))

        actions_grid = ctk.CTkFrame(card_actions, fg_color="transparent")
        actions_grid.pack(fill="x", padx=12, pady=(0, 12))
        actions_grid.grid_columnconfigure((0, 1), weight=1)

        tiles = [
            ("➕ Point of Sale", "orders", palette["accent"]),
            ("🍽️ Menu Catalog", "menu", palette["text_primary"]),
            ("📈 Sales Reports", "reports", palette["accent"]),
            ("⚙️ System Settings", "settings", palette["text_secondary"])
        ]
        for idx, (title, nav_target, color) in enumerate(tiles):
            row = idx // 2
            col = idx % 2
            btn = ctk.CTkButton(
                actions_grid,
                text=title,
                height=36,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["bg_secondary"],
                hover_color=palette["border"],
                text_color=color,
                command=lambda t=nav_target: self.navigate(t)
            )
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

    def set_left_chart(self, chart_type: str):
        self.left_chart_type = chart_type
        palette = theme_manager.get_palette()
        if hasattr(self, "btn_chart_daily") and hasattr(self, "btn_chart_monthly"):
            if chart_type == "daily":
                self.btn_chart_daily.configure(fg_color=palette["accent"], text_color="#FFFFFF")
                self.btn_chart_monthly.configure(fg_color=palette["bg_secondary"], text_color=palette["text_primary"])
            else:
                self.btn_chart_daily.configure(fg_color=palette["bg_secondary"], text_color=palette["text_primary"])
                self.btn_chart_monthly.configure(fg_color=palette["accent"], text_color="#FFFFFF")
        self._render_admin_charts()

    def set_right_chart(self, chart_type: str):
        self.right_chart_type = chart_type
        palette = theme_manager.get_palette()
        if hasattr(self, "btn_chart_pay") and hasattr(self, "btn_chart_orders") and hasattr(self, "btn_chart_staff"):
            self.btn_chart_pay.configure(
                fg_color=palette["accent"] if chart_type == "payment" else palette["bg_secondary"],
                text_color="#FFFFFF" if chart_type == "payment" else palette["text_primary"]
            )
            self.btn_chart_orders.configure(
                fg_color=palette["accent"] if chart_type == "orders" else palette["bg_secondary"],
                text_color="#FFFFFF" if chart_type == "orders" else palette["text_primary"]
            )
            self.btn_chart_staff.configure(
                fg_color=palette["accent"] if chart_type == "staff" else palette["bg_secondary"],
                text_color="#FFFFFF" if chart_type == "staff" else palette["text_primary"]
            )
        self._render_admin_charts()

    def _render_admin_charts(self):
        if not hasattr(self, "chart_left_container") or not hasattr(self, "chart_right_container"):
            return
        theme = theme_manager.get_current_theme()

        # Render Left Chart
        self._cleanup_left_chart()
        try:
            if self.left_chart_type == "daily":
                self.fig_left = report_service.plot_daily_sales(theme=theme, days=7)
            else:
                self.fig_left = report_service.plot_monthly_sales(theme=theme, months=6)

            self.chart_left_canvas = FigureCanvasTkAgg(self.fig_left, master=self.chart_left_container)
            self.chart_left_canvas.draw()
            self.chart_left_canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception:
            pass

        # Render Right Chart
        self._cleanup_right_chart()
        try:
            if self.right_chart_type == "payment":
                self.fig_right = report_service.plot_payment_methods(theme=theme)
            elif self.right_chart_type == "orders":
                self.fig_right = report_service.plot_order_status(theme=theme)
            else:
                self.fig_right = report_service.plot_staff_activity(theme=theme)

            self.chart_right_canvas = FigureCanvasTkAgg(self.fig_right, master=self.chart_right_container)
            self.chart_right_canvas.draw()
            self.chart_right_canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception:
            pass

    # =========================================================================
    # 2. CASHIER DASHBOARD — SIMPLE, FAST & FOCUSED
    # =========================================================================
    def _build_cashier_dashboard(self, palette: dict):
        user_name = self.auth_svc.current_user.full_name if self.auth_svc.current_user else "Cashier"

        # Fast CTA Banner on Top
        banner = ctk.CTkFrame(self, fg_color=palette["accent_light"], corner_radius=10, border_width=1, border_color=palette["border"])
        banner.pack(fill="x", padx=24, pady=(18, 12))

        b_left = ctk.CTkFrame(banner, fg_color="transparent")
        b_left.pack(side="left", padx=18, pady=12)

        ctk.CTkLabel(
            b_left,
            text=f"👋 Welcome, {user_name} (Counter Terminal #1)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["accent"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            b_left,
            text="Fast Cashier Terminal • Ready to take customer orders, settle bills and print receipts",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        b_right = ctk.CTkFrame(banner, fg_color="transparent")
        b_right.pack(side="right", padx=18)

        # Prominent Big Action: Start New Order
        btn_start = ctk.CTkButton(
            b_right,
            text="🚀 START NEW ORDER (Alt+N)",
            height=40,
            width=210,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            text_color="#FFFFFF",
            command=lambda: self.navigate("orders")
        )
        btn_start.pack(side="right", padx=4)

        # 4 Operational Shift KPI Cards
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_cashier")

        self.lbl_c_sales, self.sub_c_sales = self._create_kpi_card(
            kpi_row, 0, "💰 My Shift Sales", f"{CURRENCY_SYMBOL}0.00", "Settled by this terminal today", "#10B981", palette
        )
        self.lbl_c_tickets, self.sub_c_tickets = self._create_kpi_card(
            kpi_row, 1, "🧾 Tickets Completed", "0", "Invoices paid today", "#3B82F6", palette
        )
        self.lbl_c_pending, self.sub_c_pending = self._create_kpi_card(
            kpi_row, 2, "⏳ Pending Orders", "0", "Unbilled tickets waiting", "#F59E0B", palette
        )
        self.lbl_c_status, self.sub_c_status = self._create_kpi_card(
            kpi_row, 3, "🖥️ Terminal Status", "READY", "Terminal online", "#8B5CF6", palette
        )

        # Main Table: Active Counter Tickets & Today's Receipts
        card_tickets = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_tickets.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        t_head = ctk.CTkFrame(card_tickets, fg_color="transparent")
        t_head.pack(fill="x", padx=18, pady=(12, 8))

        ctk.CTkLabel(
            t_head,
            text="Today's Counter Tickets & Receipts",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        ctk.CTkButton(
            t_head,
            text="Open Receipts History →",
            width=150,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            command=lambda: self.navigate("orders_history")
        ).pack(side="right")

        self.cashier_ticket_scroll = ctk.CTkScrollableFrame(card_tickets, fg_color="transparent")
        self.cashier_ticket_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    # =========================================================================
    # 3. MANAGER DASHBOARD — FLOOR OPERATIONS & 86 DISHES
    # =========================================================================
    def _build_manager_dashboard(self, palette: dict):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="📋 Restaurant Floor Operations",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Floor shift oversight • Active table orders, turnaround monitoring and menu availability",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="🔄 Refresh Floor",
            width=100,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_data
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            actions_box,
            text="📋 Menu Catalog (86)",
            width=140,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["accent"],
            command=lambda: self.navigate("menu")
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            actions_box,
            text="➕ New Order",
            width=105,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("orders")
        ).pack(side="left", padx=3)

        # 4 Floor KPI Cards
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=24, pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi_manager")

        self.lbl_m_rev, self.sub_m_rev = self._create_kpi_card(
            kpi_row, 0, "💰 Today's Floor Revenue", f"{CURRENCY_SYMBOL}0.00", "0 tickets closed today", "#10B981", palette
        )
        self.lbl_m_pending, self.sub_m_pending = self._create_kpi_card(
            kpi_row, 1, "⏳ Kitchen/Table Pending", "0", "Active unbilled orders", "#F59E0B", palette
        )
        self.lbl_m_oos, self.sub_m_oos = self._create_kpi_card(
            kpi_row, 2, "🚫 86 List (Out of Stock)", "0 Dishes", "Unavailable for orders", "#EF4444", palette
        )
        self.lbl_m_total_menu, self.sub_m_total_menu = self._create_kpi_card(
            kpi_row, 3, "🍽️ Total Menu Catalog", "0 Dishes", "Available catalog", "#8B5CF6", palette
        )

        # Split Lower Grid: Left (Active Table Queue 60%), Right (Manager tools 40%)
        grid_split = ctk.CTkFrame(self, fg_color="transparent")
        grid_split.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        grid_split.grid_columnconfigure(0, weight=3, uniform="mgr_split")
        grid_split.grid_columnconfigure(1, weight=2, uniform="mgr_split")
        grid_split.grid_rowconfigure(0, weight=1)

        # Left Column: Active Table Queue
        card_queue = ctk.CTkFrame(grid_split, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_queue.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        q_head = ctk.CTkFrame(card_queue, fg_color="transparent")
        q_head.pack(fill="x", padx=16, pady=(12, 8))

        ctk.CTkLabel(
            q_head,
            text="Active Table & Pending Orders Queue",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        self.mgr_queue_scroll = ctk.CTkScrollableFrame(card_queue, fg_color="transparent")
        self.mgr_queue_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right Column: Manager Operational Tools
        card_tools = ctk.CTkFrame(grid_split, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card_tools.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            card_tools,
            text="Floor Management Tools",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=16, pady=(12, 10))

        tools_list = [
            ("📋 Dish Availability (86 Toggle)", "Toggle out-of-stock items instantly", "menu"),
            ("🛒 Assist Cashier Billing", "Open Point-of-Sale counter to take orders", "orders"),
            ("📜 Table Order Monitoring", "View all pending and settled tickets", "orders_history"),
            ("📈 Shift Sales Closeout", "Review end-of-shift sales and figures", "reports")
        ]

        for title, desc, target in tools_list:
            row_box = ctk.CTkFrame(card_tools, fg_color=palette["bg_secondary"], corner_radius=8)
            row_box.pack(fill="x", padx=14, pady=4)

            t_col = ctk.CTkFrame(row_box, fg_color="transparent")
            t_col.pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(t_col, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(t_col, text=desc, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")

            ctk.CTkButton(
                row_box,
                text="Open →",
                width=65,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=palette["accent"],
                hover_color=palette["accent_hover"],
                command=lambda t=target: self.navigate(t)
            ).pack(side="right", padx=10)

    # =========================================================================
    # 4. CHEF DASHBOARD — KITCHEN EXPEDITER & 86 LIST
    # =========================================================================
    def _build_chef_dashboard(self, palette: dict):
        self.chef_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.chef_scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(self.chef_scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="👨‍🍳 Kitchen Display & Order Expediter",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Live kitchen ticket queue, preparation timing, and instant 86 stockout controls",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="⚡ Kitchen Display (KDS)",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("active_orders")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="🚫 86 Stockout List",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=lambda: self.navigate("food_availability")
        ).pack(side="left", padx=4)

        # Quick Links Card
        card = ctk.CTkFrame(self.chef_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        c_inner = ctk.CTkFrame(card, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            c_inner,
            text="🍳 Kitchen Station Ready",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette["accent"]
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            c_inner,
            text="Select an action below to view active cooking orders or mark out-of-stock items:",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(0, 16))

        btn_row = ctk.CTkFrame(c_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="⚡ Open Full Kitchen Screen",
            height=40,
            width=220,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("active_orders")
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="🚫 Manage 86 Out of Stock List",
            height=40,
            width=240,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=lambda: self.navigate("food_availability")
        ).pack(side="left")

    # =========================================================================
    # 5. CUSTOMER DASHBOARD — DINING GUEST PORTAL
    # =========================================================================
    def _build_customer_dashboard(self, palette: dict):
        self.cust_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cust_scroll.pack(fill="both", expand=True)

        header = ctk.CTkFrame(self.cust_scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 12))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="🍽️ Welcome to TQM Dining Experience",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Explore our gourmet dishes, view pricing, and share your dining feedback (Q08)",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="🍽️ Browse Food Menu",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("orders")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="⭐ Submit Feedback",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=lambda: self.navigate("feedback")
        ).pack(side="left", padx=4)

        # Welcome Card
        card = ctk.CTkFrame(self.cust_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        c_inner = ctk.CTkFrame(card, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            c_inner,
            text="✨ Excellence in Hospitality & Fresh Cuisine",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette["accent"]
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            c_inner,
            text="Browse our live food catalog, inspect item pricing, or tell us how we can serve you better:",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(0, 16))

        btn_row = ctk.CTkFrame(c_inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text="🍽️ Explore Menu Catalog",
            height=40,
            width=220,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=lambda: self.navigate("orders")
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_row,
            text="⭐ Share Guest Feedback",
            height=40,
            width=220,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=lambda: self.navigate("feedback")
        ).pack(side="left")

    # =========================================================================
    # HELPER: REUSABLE KPI CARD
    # =========================================================================
    def _create_kpi_card(
        self,
        parent,
        col: int,
        title: str,
        default_val: str,
        subtitle: str,
        accent_color: str,
        palette: dict,
        row: int = 0,
        columnspan: int = 1,
        pady: tuple = (0, 0)
    ):
        card = ctk.CTkFrame(parent, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        card.grid(row=row, column=col, columnspan=columnspan, padx=5, pady=pady, sticky="nsew")

        # Top Accent Strip
        accent_strip = ctk.CTkFrame(card, height=4, fg_color=accent_color, corner_radius=0)
        accent_strip.pack(fill="x")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=(10, 10))

        ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=default_val, font=ctk.CTkFont(size=18, weight="bold"), text_color=palette.get("heading", palette["text_primary"]))
        val_lbl.pack(anchor="w", pady=(2, 2))
        sub_lbl = ctk.CTkLabel(inner, text=subtitle, font=ctk.CTkFont(size=9), text_color=palette["text_secondary"])
        sub_lbl.pack(anchor="w")

        return val_lbl, sub_lbl

    # =========================================================================
    # DATA REFRESH LOGIC (ROLE SPECIFIC)
    # =========================================================================
    def refresh_data(self):
        palette = theme_manager.get_palette()

        if self.role == "CASHIER":
            user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else None
            metrics = self.dashboard_svc.get_cashier_metrics(user_id)
            if hasattr(self, "lbl_c_sales"):
                self.lbl_c_sales.configure(text=f"{CURRENCY_SYMBOL}{metrics['shift_sales']}")
                self.lbl_c_tickets.configure(text=str(metrics["shift_tickets"]))
                self.lbl_c_pending.configure(text=str(metrics["pending_count"]))
                self.lbl_c_status.configure(text="READY")

            if hasattr(self, "cashier_ticket_scroll"):
                for child in self.cashier_ticket_scroll.winfo_children():
                    child.destroy()
                tickets = metrics.get("recent_tickets", [])
                if not tickets:
                    ctk.CTkLabel(self.cashier_ticket_scroll, text="No counter tickets registered today yet.", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(pady=20)
                else:
                    for t in tickets:
                        row = ctk.CTkFrame(self.cashier_ticket_scroll, fg_color=palette["bg_secondary"], corner_radius=6)
                        row.pack(fill="x", pady=3)
                        left = ctk.CTkFrame(row, fg_color="transparent")
                        left.pack(side="left", padx=10, pady=6)
                        ctk.CTkLabel(left, text=f"{t['order_number']}  •  {t['customer']} ({t['table']})", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
                        ctk.CTkLabel(left, text=f"Status: {t['status']}  |  {t['payment_method']}  |  {t['created_at'] or ''}", font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

                        right = ctk.CTkFrame(row, fg_color="transparent")
                        right.pack(side="right", padx=10)
                        ctk.CTkLabel(right, text=f"{CURRENCY_SYMBOL}{t['total']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["success"]).pack(side="left", padx=10)

        elif self.role == "MANAGER":
            metrics = self.dashboard_svc.get_manager_metrics()
            if hasattr(self, "lbl_m_rev"):
                self.lbl_m_rev.configure(text=f"{CURRENCY_SYMBOL}{metrics['floor_revenue']}")
                self.sub_m_rev.configure(text=f"{metrics['orders_today']} tickets closed today")
                self.lbl_m_pending.configure(text=str(metrics["pending_count"]))
                self.lbl_m_oos.configure(text=f"{metrics['oos_count']} Dishes")
                self.lbl_m_total_menu.configure(text=f"{metrics['total_items']} Dishes")

            if hasattr(self, "mgr_queue_scroll"):
                for child in self.mgr_queue_scroll.winfo_children():
                    child.destroy()
                queue = metrics.get("pending_orders", [])
                if not queue:
                    ctk.CTkLabel(self.mgr_queue_scroll, text="All tables clear! No pending orders in queue.", font=ctk.CTkFont(size=11), text_color=palette["success"]).pack(pady=20)
                else:
                    for q in queue:
                        row = ctk.CTkFrame(self.mgr_queue_scroll, fg_color=palette["bg_secondary"], corner_radius=6)
                        row.pack(fill="x", pady=3)
                        left = ctk.CTkFrame(row, fg_color="transparent")
                        left.pack(side="left", padx=10, pady=6)
                        ctk.CTkLabel(left, text=f"{q['order_number']}  •  Table: {q['table']} ({q['customer']})", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
                        ctk.CTkLabel(left, text=f"{q['items']} Items  |  Placed: {q['created_at'] or ''}", font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

                        btn_settle = ctk.CTkButton(
                            row,
                            text="Settle Bill →",
                            width=80,
                            height=26,
                            font=ctk.CTkFont(size=10, weight="bold"),
                            fg_color=palette["accent"],
                            hover_color=palette["accent_hover"],
                            command=lambda: self.navigate("orders_history")
                        )
                        btn_settle.pack(side="right", padx=10)

        elif self.role in ["CHEF", "CUSTOMER"]:
            pass
        else:
            # ADMIN
            metrics = self.dashboard_svc.get_admin_metrics()
            if hasattr(self, "lbl_admin_staff"):
                self.lbl_admin_staff.configure(text=str(metrics["total_staff"]))
                self.sub_admin_staff.configure(text=f"{metrics['total_staff']} accounts registered")
            if hasattr(self, "lbl_admin_active_users"):
                self.lbl_admin_active_users.configure(text=str(metrics["active_users"]))
                self.sub_admin_active_users.configure(text=f"{metrics['active_users']} active in system")
            if hasattr(self, "lbl_admin_total_orders"):
                self.lbl_admin_total_orders.configure(text=str(metrics["total_orders"]))
                self.sub_admin_total_orders.configure(text=f"{metrics['total_orders']} all-time orders")
            if hasattr(self, "lbl_admin_total_sales"):
                self.lbl_admin_total_sales.configure(text=f"{CURRENCY_SYMBOL}{metrics['total_sales']}")
                self.sub_admin_total_sales.configure(text="Gross settled revenue")
            if hasattr(self, "lbl_admin_txns"):
                self.lbl_admin_txns.configure(text=str(metrics["total_transactions"]))
                self.sub_admin_txns.configure(text=f"{metrics['total_transactions']} paid receipts")
            if hasattr(self, "lbl_admin_pending"):
                self.lbl_admin_pending.configure(text=str(metrics["pending_orders"]))
                self.sub_admin_pending.configure(text=f"{metrics['pending_orders']} awaiting settlement")
            if hasattr(self, "lbl_admin_sys_status"):
                self.lbl_admin_sys_status.configure(text=metrics["system_status"])
                self.sub_admin_sys_status.configure(text="SQLite engine operational • 0 errors")

            # Redraw Live Visual Charts
            self._render_admin_charts()

            # Update Channel Breakdown
            if hasattr(self, "box_channels"):
                for child in self.box_channels.winfo_children():
                    child.destroy()
                channels = metrics.get("payment_breakdown", {})
                for ch, amt in channels.items():
                    r = ctk.CTkFrame(self.box_channels, fg_color="transparent")
                    r.pack(fill="x", pady=2)
                    ctk.CTkLabel(r, text=f"• {ch}:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
                    ctk.CTkLabel(r, text=f"{CURRENCY_SYMBOL}{amt}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["accent"]).pack(side="right")

            # Update Recent Transactions
            if hasattr(self, "admin_txn_scroll"):
                for child in self.admin_txn_scroll.winfo_children():
                    child.destroy()
                txns = metrics.get("recent_transactions", [])
                if not txns:
                    ctk.CTkLabel(self.admin_txn_scroll, text="No transactions recorded yet.", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(pady=20)
                else:
                    for t in txns:
                        row = ctk.CTkFrame(self.admin_txn_scroll, fg_color=palette["bg_secondary"], corner_radius=6)
                        row.pack(fill="x", pady=3)

                        left = ctk.CTkFrame(row, fg_color="transparent")
                        left.pack(side="left", padx=10, pady=6)
                        ctk.CTkLabel(left, text=f"{t['order_number']}  •  {t['customer']} ({t['table']})", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
                        ctk.CTkLabel(left, text=f"Cashier: {t['staff']}  |  {t['payment_method']}  |  {t['created_at'] or ''}", font=ctk.CTkFont(size=9), text_color=palette["text_secondary"]).pack(anchor="w")

                        right = ctk.CTkFrame(row, fg_color="transparent")
                        right.pack(side="right", padx=10)
                        st_color = palette["success"] if t["status"] == "COMPLETED" else palette["warning"]
                        ctk.CTkLabel(right, text=t["status"], font=ctk.CTkFont(size=9, weight="bold"), text_color=st_color).pack(anchor="e")
                        ctk.CTkLabel(right, text=f"{CURRENCY_SYMBOL}{t['amount']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="e")
