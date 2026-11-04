"""Cashier Billing Queue: Dedicated management of unbilled customer dining and takeaway orders."""
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import customtkinter as ctk

from ui.theme_manager import theme_manager
from services.order_service import OrderService, order_service
from services.billing_service import BillingService, billing_service
from config.settings import CURRENCY_SYMBOL
from utils.window_utils import center_dialog
from utils.logger import logger


class OrderDetailsDialog(ctk.CTkToplevel):
    """Modal displaying full itemized breakdown and audit timestamps for a customer order."""

    def __init__(self, master, order_data: Dict[str, Any], on_proceed_to_bill: Optional[Callable[[int], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.order_data = order_data
        self.on_proceed_to_bill = on_proceed_to_bill

        self.title(f"Order #{order_data['order_number']} Details")
        self.resizable(False, False)
        center_dialog(self, master, target_width=520, target_height=540)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Top Header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(
            head,
            text=f"📋 Order #{self.order_data['order_number']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        sub = f"Customer: {self.order_data['customer_name']}  |  Table: {self.order_data['table_number']}"
        ctk.CTkLabel(
            head,
            text=sub,
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Status Grid Card
        status_card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        status_card.pack(fill="x", padx=24, pady=(0, 12))
        status_card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(status_card, text=f"👨‍🍳 Kitchen Status: {self.order_data['kitchen_status']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).grid(row=0, column=0, padx=12, pady=6, sticky="w")
        ctk.CTkLabel(status_card, text=f"🍽️ Serving Status: {self.order_data['serving_status']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["accent"]).grid(row=0, column=1, padx=12, pady=6, sticky="w")
        ctk.CTkLabel(status_card, text=f"💳 Billing Status: {self.order_data['billing_status']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["warning"]).grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ctk.CTkLabel(status_card, text=f"💵 Payment Status: {self.order_data['payment_status']}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=1, padx=12, pady=6, sticky="w")

        # Items List
        items_card = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        items_card.pack(fill="both", expand=True, padx=24, pady=(0, 14))

        ctk.CTkLabel(
            items_card,
            text="Itemized Order Contents",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w", padx=14, pady=(10, 6))

        scroll = ctk.CTkScrollableFrame(items_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        items = self.order_data.get("items", [])
        for it in items:
            row = ctk.CTkFrame(scroll, fg_color=palette["bg_secondary"], corner_radius=6)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{it.item_name}  ×{it.quantity}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=f"{CURRENCY_SYMBOL}{it.line_total}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["success"]).pack(side="right", padx=10)

        # Bottom Total & Action
        b_bar = ctk.CTkFrame(self, fg_color="transparent")
        b_bar.pack(fill="x", padx=24, pady=(0, 20))

        tot_box = ctk.CTkFrame(b_bar, fg_color="transparent")
        tot_box.pack(side="left")

        ctk.CTkLabel(tot_box, text=f"Total: {CURRENCY_SYMBOL}{self.order_data['total_amount']}", font=ctk.CTkFont(size=16, weight="bold"), text_color=palette["success"]).pack(anchor="w")

        ctk.CTkButton(
            b_bar,
            text="Close",
            width=90,
            height=34,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        if self.order_data.get("bill_id") is None and self.on_proceed_to_bill:
            ctk.CTkButton(
                b_bar,
                text="Generate Bill 💳",
                width=140,
                height=34,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"],
                hover_color=palette["accent_hover"],
                text_color="#FFFFFF",
                command=lambda: (self.destroy(), self.on_proceed_to_bill(self.order_data["id"]))
            ).pack(side="right")


class CashierBillingQueueFrame(ctk.CTkFrame):
    """Customer Orders — Pending Billing queue interface for Cashier and Floor Management."""

    def __init__(
        self,
        master,
        on_generate_bill: Callable[[int], None],
        on_view_receipt: Optional[Callable[[int], None]] = None,
        order_svc: OrderService = order_service,
        billing_svc: BillingService = billing_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_generate_bill = on_generate_bill
        self.on_view_receipt = on_view_receipt
        self.order_svc = order_svc
        self.billing_svc = billing_svc

        self.current_filter: str = "ALL_UNBILLED"
        self.search_query: str = ""

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_queue()

    def destroy(self):
        theme_manager.unsubscribe(self.on_theme_changed)
        super().destroy()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_queue()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # 1. Header with Title and Search Bar
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💳 Customer Orders — Pending Billing",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Live cashier billing queue • Settle customer dining & counter orders regardless of kitchen or serving progress",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w", pady=(2, 0))

        # Controls Right: Search + Refresh
        ctrl_box = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_box.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            ctrl_box,
            placeholder_text="🔍 Search Order ID, Customer, Table...",
            width=260,
            height=34,
            font=ctk.CTkFont(size=11)
        )
        self.search_entry.pack(side="left", padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        ctk.CTkButton(
            ctrl_box,
            text="Clear",
            width=60,
            height=34,
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=self._clear_search
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            ctrl_box,
            text="🔄 Refresh Queue",
            width=130,
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            text_color="#FFFFFF",
            command=self.refresh_queue
        ).pack(side="right")

        # 2. KPI Summary Bar (4 Cards)
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=24, pady=(0, 12))
        self.kpi_container.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="billing_kpi")

        self.card_total_unbilled = self._build_kpi_card(0, "⏳ Total Unbilled", "0", "Orders awaiting bill", "#F59E0B")
        self.card_served = self._build_kpi_card(1, "✅ Served & Ready", "0", "Delivered to diners", "#10B981")
        self.card_ready = self._build_kpi_card(2, "🔔 Kitchen Ready", "0", "Prepared at pass", "#3B82F6")
        self.card_value = self._build_kpi_card(3, "💰 Unbilled Value", f"{CURRENCY_SYMBOL}0.00", "Pending settlement", "#8B5CF6")

        # 3. Filter Segmented Tabs
        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.pack(fill="x", padx=24, pady=(0, 10))

        self.filter_buttons = {}
        filters_def = [
            ("ALL_UNBILLED", "📋 All Unbilled"),
            ("SERVED", "✅ Served (Ready to Bill)"),
            ("READY", "🔔 Kitchen Ready"),
            ("PICKED_UP", "🚶 In Transit"),
            ("IN_KITCHEN", "👨‍🍳 In Kitchen"),
            ("ALL_ORDERS", "📜 All Orders")
        ]
        for key, label in filters_def:
            btn = ctk.CTkButton(
                filter_row,
                text=label,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"] if key == self.current_filter else palette["bg_card"],
                text_color="#FFFFFF" if key == self.current_filter else palette["text_secondary"],
                border_width=1,
                border_color=palette["border"],
                hover_color=palette["accent_hover"],
                command=lambda k=key: self._set_filter(k)
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[key] = btn

        # 4. Scrollable Container for Queue Cards
        self.scroll_orders = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=palette.get("sidebar_hover", "#245A9B")
        )
        self.scroll_orders.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _build_kpi_card(self, col: int, title: str, initial_val: str, subtitle: str, color: str):
        palette = theme_manager.get_palette()
        card = ctk.CTkFrame(self.kpi_container, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        card.grid(row=0, column=col, padx=4, sticky="nsew")

        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=color).pack(anchor="w", padx=12, pady=(8, 1))
        lbl_val = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(size=20, weight="bold"), text_color=palette.get("heading", palette["text_primary"]))
        lbl_val.pack(anchor="w", padx=12)
        lbl_sub = ctk.CTkLabel(card, text=subtitle, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"])
        lbl_sub.pack(anchor="w", padx=12, pady=(0, 8))
        return lbl_val

    def _on_search_key(self, _event=None):
        self.search_query = self.search_entry.get().strip()
        self.refresh_queue()

    def _clear_search(self):
        self.search_entry.delete(0, "end")
        self.search_query = ""
        self.refresh_queue()

    def _set_filter(self, filter_key: str):
        self.current_filter = filter_key
        palette = theme_manager.get_palette()
        for k, btn in self.filter_buttons.items():
            if k == filter_key:
                btn.configure(fg_color=palette["accent"], text_color="#FFFFFF")
            else:
                btn.configure(fg_color=palette["bg_card"], text_color=palette["text_secondary"])
        self.refresh_queue()

    def refresh_queue(self):
        """Fetches eligible unbilled orders and renders billing cards with independent statuses."""
        palette = theme_manager.get_palette()

        try:
            # Query unbilled orders with rich metadata
            orders = self.order_svc.get_pending_billing_orders(
                search_query=self.search_query,
                filter_status=self.current_filter,
                limit=100
            )
            # Query all unbilled orders for KPI telemetry
            all_unbilled = self.order_svc.get_pending_billing_orders(
                search_query=None,
                filter_status="ALL_UNBILLED",
                limit=500
            )
        except Exception as e:
            logger.error(f"Error fetching pending billing queue: {e}")
            orders = []
            all_unbilled = []

        # Update KPI metrics
        total_cnt = len(all_unbilled)
        served_cnt = len([o for o in all_unbilled if o["serving_status"] == "SERVED"])
        ready_cnt = len([o for o in all_unbilled if o["kitchen_status"] == "READY"])
        total_val = sum((o["total_amount"] for o in all_unbilled), Decimal("0.00"))

        if hasattr(self, "card_total_unbilled"):
            self.card_total_unbilled.configure(text=str(total_cnt))
            self.card_served.configure(text=str(served_cnt))
            self.card_ready.configure(text=str(ready_cnt))
            self.card_value.configure(text=f"{CURRENCY_SYMBOL}{total_val:,.2f}")

        # Clear existing cards
        for child in self.scroll_orders.winfo_children():
            child.destroy()

        if not orders:
            empty_box = ctk.CTkFrame(self.scroll_orders, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            empty_box.pack(fill="x", pady=40, padx=20)

            ctk.CTkLabel(
                empty_box,
                text="✨ No Pending Unbilled Orders Found",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=palette.get("heading", palette["text_primary"])
            ).pack(pady=(28, 4))

            ctk.CTkLabel(
                empty_box,
                text="All active customer dining orders and takeaway counter orders have been settled.\nNew orders placed by customers or floor servers will instantly appear here.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"],
                justify="center"
            ).pack(pady=(0, 28))
            return

        # Render Order Cards
        for o in orders:
            self._render_order_card(o, palette)

    def _render_order_card(self, o: Dict[str, Any], palette: dict):
        is_served = (o["serving_status"] == "SERVED")
        is_ready = (o["kitchen_status"] == "READY")
        is_unbilled = (o["bill_id"] is None)

        # Highlight served orders awaiting bill with prominent subtle border
        border_col = palette["accent"] if (is_served and is_unbilled) else palette["border"]
        card = ctk.CTkFrame(
            self.scroll_orders,
            fg_color=palette["bg_card"],
            corner_radius=10,
            border_width=1 if not (is_served and is_unbilled) else 2,
            border_color=border_col
        )
        card.pack(fill="x", pady=5)

        # Inner 2-column layout: Left details & statuses, Right total & actions
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        # LEFT SIDE: Order Details
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)

        # Top line: Order Number, Customer, Table
        top_line = ctk.CTkFrame(left, fg_color="transparent")
        top_line.pack(fill="x", anchor="w")

        ctk.CTkLabel(
            top_line,
            text=f"#{o['order_number']}",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        ctk.CTkLabel(
            top_line,
            text=f"  •  Table: {o['table_number']}  •  Customer: {o['customer_name']}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        if is_served and is_unbilled:
            badge_ready_bill = ctk.CTkFrame(top_line, fg_color=palette["accent"], corner_radius=4)
            badge_ready_bill.pack(side="left", padx=8)
            ctk.CTkLabel(badge_ready_bill, text="READY FOR BILLING", font=ctk.CTkFont(size=9, weight="bold"), text_color="#FFFFFF").pack(padx=6, pady=2)

        # Second line: Timestamp, Server/Waiter info
        meta_line = ctk.CTkFrame(left, fg_color="transparent")
        meta_line.pack(fill="x", anchor="w", pady=(2, 6))

        waiter_display = f"Floor Server: {o['waiter_name']}" if o.get("waiter_name") and o["waiter_name"] != "Unassigned" else "Floor Server: Unassigned"
        ctk.CTkLabel(
            meta_line,
            text=f"Ordered: {o['created_at']}  |  {waiter_display}",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"]
        ).pack(side="left")

        # Third line: 4 Independent Status Badges
        status_row = ctk.CTkFrame(left, fg_color="transparent")
        status_row.pack(fill="x", anchor="w", pady=(0, 6))

        # 1. Kitchen Status Badge
        k_col = palette["success"] if o["kitchen_status"] == "READY" else (palette["warning"] if o["kitchen_status"] == "PREPARING" else palette["text_secondary"])
        self._add_status_pill(status_row, f"👨‍🍳 Kitchen: {o['kitchen_status']}", k_col, palette)

        # 2. Serving Status Badge
        s_col = palette["accent"] if o["serving_status"] == "SERVED" else (palette["warning"] if o["serving_status"] == "PICKED_UP" else palette["text_secondary"])
        self._add_status_pill(status_row, f"🍽️ Serving: {o['serving_status']}", s_col, palette)

        # 3. Billing Status Badge
        b_col = palette["success"] if o["billing_status"] == "SETTLED" else palette["warning"]
        self._add_status_pill(status_row, f"💳 Billing: {o['billing_status']}", b_col, palette)

        # 4. Payment Status Badge
        p_col = palette["success"] if o["payment_status"] == "PAID" else palette["warning"]
        self._add_status_pill(status_row, f"💵 Payment: {o['payment_status']}", p_col, palette)

        # Fourth line: Items Summary
        ctk.CTkLabel(
            left,
            text=f"Items: {o['items_summary']}",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_primary"]
        ).pack(anchor="w")

        if o.get("special_instructions"):
            ctk.CTkLabel(
                left,
                text=f"Note: \"{o['special_instructions']}\"",
                font=ctk.CTkFont(size=10, slant="italic"),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", pady=(1, 0))

        # RIGHT SIDE: Amount & Action Buttons
        right = ctk.CTkFrame(card, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nse", padx=16, pady=12)

        # Total Price Display
        ctk.CTkLabel(
            right,
            text=f"{CURRENCY_SYMBOL}{o['total_amount']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["success"]
        ).pack(anchor="e", pady=(0, 8))

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.pack(anchor="e")

        # View Order Button
        ctk.CTkButton(
            actions,
            text="View 👁️",
            width=70,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=lambda od=o: OrderDetailsDialog(self.winfo_toplevel(), od, on_proceed_to_bill=self.on_generate_bill)
        ).pack(side="left", padx=(0, 6))

        # Primary Action: Generate Bill or View Receipt
        if is_unbilled:
            ctk.CTkButton(
                actions,
                text="Generate Bill 💳",
                width=135,
                height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"],
                hover_color=palette["accent_hover"],
                text_color="#FFFFFF",
                command=lambda oid=o["id"]: self.on_generate_bill(oid)
            ).pack(side="left")
        else:
            ctk.CTkButton(
                actions,
                text="View Receipt 🧾",
                width=120,
                height=32,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["bg_secondary"],
                text_color=palette["text_primary"],
                hover_color=palette["border"],
                command=lambda oid=o["id"]: self.on_view_receipt(oid) if self.on_view_receipt else None
            ).pack(side="left")

    def _add_status_pill(self, parent: ctk.CTkFrame, text: str, text_color: str, palette: dict):
        pill = ctk.CTkFrame(parent, fg_color=palette["bg_secondary"], corner_radius=6, border_width=1, border_color=text_color)
        pill.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            pill,
            text=text,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=text_color
        ).pack(padx=6, pady=2)
