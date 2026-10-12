"""Visual Reports view embedding Matplotlib analytical charts in CustomTkinter (Q08-F2)."""
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from services.report_service import ReportService, report_service
from ui.theme_manager import theme_manager


class ReportsFrame(ctk.CTkFrame):
    """Analytics and statistical reports view with interactive Matplotlib figures."""

    def __init__(self, master, report_svc: ReportService = report_service, **kwargs):
        super().__init__(master, **kwargs)
        self.report_svc = report_svc
        self.current_days = 7
        self._canvases = []

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_charts()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_charts()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header and filter bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="📈 Visual Analytics & Quality Reports",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Data-driven statistical analysis for operational excellence (TQM)",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")

        ctk.CTkLabel(controls, text="Period:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(side="left", padx=(0, 6))

        self.period_seg = ctk.CTkSegmentedButton(
            controls,
            values=["7 Days", "14 Days", "30 Days"],
            command=self._on_period_changed
        )
        self.period_seg.set("7 Days")
        self.period_seg.pack(side="left", padx=(0, 10))

        refresh_btn = ctk.CTkButton(
            controls,
            text="🔄 Refresh Charts",
            width=110,
            height=32,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.refresh_charts
        )
        refresh_btn.pack(side="left")

        # Scrollable grid for 4 charts (2x2 grid)
        self.charts_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.charts_container.grid_columnconfigure((0, 1), weight=1, uniform="charts")
        self.charts_container.grid_rowconfigure((0, 1), weight=1)

        # 4 Card Containers
        self.card_sales = ctk.CTkFrame(self.charts_container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.card_sales.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.card_items = ctk.CTkFrame(self.charts_container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.card_items.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.card_status = ctk.CTkFrame(self.charts_container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.card_status.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.card_pay = ctk.CTkFrame(self.charts_container, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        self.card_pay.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    def _on_period_changed(self, value: str):
        days_map = {"7 Days": 7, "14 Days": 14, "30 Days": 30}
        self.current_days = days_map.get(value, 7)
        self.refresh_charts()

    def _render_chart_in_card(self, card_frame: ctk.CTkFrame, figure):
        # Clear previous canvas inside card
        for child in card_frame.winfo_children():
            child.destroy()

        canvas = FigureCanvasTkAgg(figure, master=card_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._canvases.append(canvas)

    def refresh_charts(self):
        """Re-queries data and embeds freshly rendered figures."""
        theme = theme_manager.current_theme

        # 1. Daily Sales Trend
        fig_sales = self.report_svc.plot_daily_sales(theme=theme, days=self.current_days)
        self._render_chart_in_card(self.card_sales, fig_sales)

        # 2. Top Selling Dishes
        fig_items = self.report_svc.plot_top_items(theme=theme, limit=6)
        self._render_chart_in_card(self.card_items, fig_items)

        # 3. Order Status Breakdown
        fig_status = self.report_svc.plot_order_status(theme=theme)
        self._render_chart_in_card(self.card_status, fig_status)

        # 4. Payment Method Distribution
        fig_pay = self.report_svc.plot_payment_methods(theme=theme)
        self._render_chart_in_card(self.card_pay, fig_pay)
