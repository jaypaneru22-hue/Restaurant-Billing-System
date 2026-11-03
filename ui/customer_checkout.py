"""Customer Checkout and Order Confirmation Dialogs for RestoPro."""
from typing import Optional, Callable, Dict, List, Tuple
from decimal import Decimal
from datetime import datetime
import customtkinter as ctk

from models.order import Order
from services.order_service import OrderService, order_service
from services.menu_service import MenuService, menu_service
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import CURRENCY_SYMBOL, DEFAULT_TAX_RATE
from utils.window_utils import center_dialog
from utils.brand_assets import apply_window_icon
from utils.logger import logger


class ConfirmClearCartDialog(ctk.CTkToplevel):
    """Confirmation modal before clearing non-empty cart."""

    def __init__(self, master, on_confirmed: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.on_confirmed = on_confirmed
        self.title("RestoPro — Clear Cart")
        self.resizable(False, False)
        center_dialog(self, master, target_width=380, target_height=200)
        self.grab_set()
        apply_window_icon(self)

        is_dark = (theme_manager.current_theme != "light")
        bg_col = "#211B30" if is_dark else "#EDE7F5"
        card_col = "#2B233B" if is_dark else "#E1D7ED"
        border_col = "#514461" if is_dark else "#CFC1DF"
        text_pri = "#FFFFFF" if is_dark else "#292039"
        text_sec = "#B9AEC9" if is_dark else "#655873"

        self.configure(fg_color=bg_col)
        card = ctk.CTkFrame(self, fg_color=card_col, corner_radius=12, border_width=1, border_color=border_col)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="🗑️ Clear Order Ticket?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=text_pri
        ).pack(anchor="w", padx=16, pady=(16, 6))

        ctk.CTkLabel(
            card,
            text="Are you sure you want to remove all selected\nfood items from your current order ticket?",
            font=ctk.CTkFont(size=11),
            text_color=text_sec,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(0, 16))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row,
            text="Keep Items",
            width=90,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=bg_col,
            text_color=text_pri,
            border_width=1,
            border_color=border_col,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Yes, Clear Cart",
            width=110,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            command=self._handle_confirm
        ).pack(side="right")

    def _handle_confirm(self):
        self.destroy()
        self.on_confirmed()


class CustomerCheckoutDialog(ctk.CTkToplevel):
    """Customer Review & Order Checkout dialog (Dine-in vs Takeaway, Special Instructions, Totals)."""

    def __init__(
        self,
        master,
        cart: Dict[int, dict],
        table_number: str,
        customer_name: str,
        on_order_confirmed: Callable[[Order], None],
        order_svc: OrderService = order_service,
        menu_svc: MenuService = menu_service,
        auth_svc: AuthService = auth_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.cart = dict(cart)
        self.table_number = table_number.strip() if table_number else "Table 1"
        self.customer_name = customer_name.strip() if customer_name else "Valued Guest"
        self.on_order_confirmed = on_order_confirmed
        self.order_svc = order_svc
        self.menu_svc = menu_svc
        self.auth_svc = auth_svc
        self._is_submitting = False

        self.title("RestoPro — Review & Place Order")
        self.resizable(False, False)
        center_dialog(self, master, target_width=520, target_height=650)
        self.grab_set()
        apply_window_icon(self)

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        is_dark = (theme_manager.current_theme != "light")

        bg_col = "#211B30" if is_dark else "#EDE7F5"
        card_col = "#2B233B" if is_dark else "#E1D7ED"
        input_col = "#171323" if is_dark else "#F1ECF6"
        border_col = "#514461" if is_dark else "#CFC1DF"
        text_pri = "#FFFFFF" if is_dark else "#292039"
        text_sec = "#B9AEC9" if is_dark else "#655873"
        accent_col = "#7653DB" if is_dark else "#6650C8"
        hover_col = "#8A6BE8" if is_dark else "#7653DB"

        self.configure(fg_color=bg_col)

        # Main scrollable canvas container
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(16, 12))

        # 1. Header
        ctk.CTkLabel(
            scroll,
            text="🛒 Review Order & Checkout",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color=text_pri
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            scroll,
            text="Please verify your dining details and selected dishes before placing order.",
            font=ctk.CTkFont(size=11),
            text_color=text_sec
        ).pack(anchor="w", pady=(0, 12))

        # 2. Dining Information Card
        dining_card = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
        dining_card.pack(fill="x", pady=(0, 12))

        d_inner = ctk.CTkFrame(dining_card, fg_color="transparent")
        d_inner.pack(fill="x", padx=14, pady=10)

        is_parcel = "parcel" in self.table_number.lower() or "takeaway" in self.table_number.lower()
        order_type_str = "📦 Takeaway / Parcel" if is_parcel else f"🍽️ Dine-in ({self.table_number})"

        d_row1 = ctk.CTkFrame(d_inner, fg_color="transparent")
        d_row1.pack(fill="x", pady=2)
        ctk.CTkLabel(d_row1, text="Order Type:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        type_pill = ctk.CTkFrame(d_row1, fg_color=input_col, corner_radius=6, border_width=1, border_color=border_col)
        type_pill.pack(side="right")
        ctk.CTkLabel(type_pill, text=order_type_str, font=ctk.CTkFont(size=11, weight="bold"), text_color=accent_col).pack(padx=8, pady=2)

        d_row2 = ctk.CTkFrame(d_inner, fg_color="transparent")
        d_row2.pack(fill="x", pady=2)
        ctk.CTkLabel(d_row2, text="Customer Name:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(d_row2, text=self.customer_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(side="right")

        # 3. Selected Items List Card
        items_card = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
        items_card.pack(fill="x", pady=(0, 12))

        i_head = ctk.CTkFrame(items_card, fg_color="transparent")
        i_head.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(i_head, text="Order Items Summary", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_pri).pack(side="left")
        ctk.CTkLabel(i_head, text=f"{len(self.cart)} dishes", font=ctk.CTkFont(size=10, weight="bold"), text_color=accent_col).pack(side="right")

        # Items listing
        subtotal = Decimal("0.00")
        for item_id, item_data in self.cart.items():
            qty = item_data["qty"]
            price = Decimal(str(item_data["price"]))
            line_tot = (price * qty).quantize(Decimal("0.01"))
            subtotal += line_tot

            it_row = ctk.CTkFrame(items_card, fg_color="transparent")
            it_row.pack(fill="x", padx=14, pady=3)

            left_box = ctk.CTkFrame(it_row, fg_color="transparent")
            left_box.pack(side="left")

            ctk.CTkLabel(
                left_box,
                text=f"• {item_data['name']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=text_pri
            ).pack(anchor="w")

            ctk.CTkLabel(
                left_box,
                text=f"  Qty: {qty} × {CURRENCY_SYMBOL}{price:.2f}",
                font=ctk.CTkFont(size=10),
                text_color=text_sec
            ).pack(anchor="w")

            ctk.CTkLabel(
                it_row,
                text=f"{CURRENCY_SYMBOL}{line_tot:.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=text_pri
            ).pack(side="right")

        ctk.CTkFrame(items_card, height=1, fg_color=border_col).pack(fill="x", padx=14, pady=(6, 8))

        # 4. Special Kitchen Instructions
        ctk.CTkLabel(
            scroll,
            text="📝 Special Kitchen Instructions (Optional)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=text_pri
        ).pack(anchor="w", pady=(0, 4))

        self.entry_instructions = ctk.CTkEntry(
            scroll,
            height=34,
            placeholder_text="e.g. Less spicy, no garlic, extra lemon slices...",
            font=ctk.CTkFont(size=11),
            fg_color=input_col,
            border_color=border_col,
            text_color=text_pri
        )
        self.entry_instructions.pack(fill="x", pady=(0, 12))

        # 5. Financial Breakdown
        est_gst = (subtotal * (DEFAULT_TAX_RATE / Decimal("100.00"))).quantize(Decimal("0.01"))
        net_total = (subtotal + est_gst).quantize(Decimal("0.01"))

        calc_card = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
        calc_card.pack(fill="x", pady=(0, 12))

        c_box = ctk.CTkFrame(calc_card, fg_color="transparent")
        c_box.pack(fill="x", padx=14, pady=10)

        r_sub = ctk.CTkFrame(c_box, fg_color="transparent")
        r_sub.pack(fill="x", pady=2)
        ctk.CTkLabel(r_sub, text="Items Subtotal:", font=ctk.CTkFont(size=11), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(r_sub, text=f"{CURRENCY_SYMBOL}{subtotal:.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_pri).pack(side="right")

        r_gst = ctk.CTkFrame(c_box, fg_color="transparent")
        r_gst.pack(fill="x", pady=2)
        ctk.CTkLabel(r_gst, text=f"Estimated GST ({DEFAULT_TAX_RATE}%):", font=ctk.CTkFont(size=11), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(r_gst, text=f"+{CURRENCY_SYMBOL}{est_gst:.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_pri).pack(side="right")

        ctk.CTkFrame(c_box, height=1, fg_color=border_col).pack(fill="x", pady=(6, 6))

        r_tot = ctk.CTkFrame(c_box, fg_color="transparent")
        r_tot.pack(fill="x", pady=2)
        ctk.CTkLabel(r_tot, text="Final Net Total:", font=ctk.CTkFont(size=14, weight="bold"), text_color=text_pri).pack(side="left")
        ctk.CTkLabel(r_tot, text=f"{CURRENCY_SYMBOL}{net_total:.2f}", font=ctk.CTkFont(size=18, weight="bold"), text_color=palette["success"]).pack(side="right")

        # 6. Pay-at-Counter Notice
        notice_box = ctk.CTkFrame(scroll, fg_color=input_col, corner_radius=8, border_width=1, border_color=border_col)
        notice_box.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            notice_box,
            text="ℹ️ Pay-at-Counter Workflow",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=accent_col
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            notice_box,
            text="Your order will be instantly dispatched to the kitchen queue for preparation.\nPayment is settled at the cashier counter upon order completion / pickup.",
            font=ctk.CTkFont(size=10),
            text_color=text_sec,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Error notification label
        self.lbl_error = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["danger"])
        self.lbl_error.pack(fill="x", pady=(0, 6))

        # Bottom Button Row
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_bar,
            text="Back to Menu",
            width=110,
            height=38,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=card_col,
            text_color=text_pri,
            border_width=1,
            border_color=border_col,
            command=self.destroy
        ).pack(side="left")

        self.btn_confirm = ctk.CTkButton(
            btn_bar,
            text="CONFIRM & PLACE ORDER ➔",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=accent_col,
            hover_color=hover_col,
            text_color="#FFFFFF",
            command=self._handle_submit_order
        )
        self.btn_confirm.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def _handle_submit_order(self):
        """Validates cart, checks stock availability, and submits order atomically."""
        if self._is_submitting:
            return

        if not self.cart:
            self.lbl_error.configure(text="Cart is empty. Please add items.")
            return

        # 1. Validate item availability and quantities
        item_entries = []
        for item_id, item_data in self.cart.items():
            qty = item_data.get("qty", 1)
            if qty <= 0:
                self.lbl_error.configure(text=f"Invalid quantity for {item_data['name']}.")
                return

            menu_item = self.menu_svc.get_item(item_id)
            if not menu_item or not menu_item.is_available:
                self.lbl_error.configure(text=f"'{item_data['name']}' is out of stock. Please remove it.")
                return

            item_entries.append((item_id, qty))

        # 2. Prevent duplicate submissions
        self._is_submitting = True
        self.btn_confirm.configure(state="disabled", text="Placing Order...")

        user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else 1
        instructions = self.entry_instructions.get().strip()

        ok, msg, order = self.order_svc.create_order(
            user_id=user_id,
            table_number=self.table_number,
            customer_name=self.customer_name,
            item_entries=item_entries,
            special_instructions=instructions
        )

        if ok and order:
            logger.info(f"Customer order successfully placed: #{order.order_number} (id={order.id})")
            self.destroy()
            self.on_order_confirmed(order)
        else:
            self._is_submitting = False
            self.btn_confirm.configure(state="normal", text="CONFIRM & PLACE ORDER ➔")
            self.lbl_error.configure(text=msg or "Failed to place order. Please try again.")


class OrderConfirmationDialog(ctk.CTkToplevel):
    """Professional order placed confirmation modal with prep time estimation and live tracking action."""

    def __init__(
        self,
        master,
        order: Order,
        on_track_order: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.order = order
        self.on_track_order = on_track_order

        self.title("RestoPro — Order Placed Successfully")
        self.resizable(False, False)
        center_dialog(self, master, target_width=500, target_height=580)
        self.grab_set()
        apply_window_icon(self)

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        is_dark = (theme_manager.current_theme != "light")

        bg_col = "#211B30" if is_dark else "#EDE7F5"
        card_col = "#2B233B" if is_dark else "#E1D7ED"
        border_col = "#514461" if is_dark else "#CFC1DF"
        text_pri = "#FFFFFF" if is_dark else "#292039"
        text_sec = "#B9AEC9" if is_dark else "#655873"
        accent_col = "#7653DB" if is_dark else "#6650C8"
        hover_col = "#8A6BE8" if is_dark else "#7653DB"

        self.configure(fg_color=bg_col)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(16, 12))

        # Success Banner
        badge_box = ctk.CTkFrame(scroll, fg_color="transparent")
        badge_box.pack(fill="x", pady=(8, 12))

        ctk.CTkLabel(badge_box, text="🎉", font=ctk.CTkFont(size=36)).pack(anchor="center")
        ctk.CTkLabel(
            badge_box,
            text="Order Placed Successfully!",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette["success"]
        ).pack(anchor="center", pady=(4, 2))

        ctk.CTkLabel(
            badge_box,
            text="Your ticket has been sent to the Kitchen Display System (KDS).",
            font=ctk.CTkFont(size=11),
            text_color=text_sec
        ).pack(anchor="center")

        # Order Details Card
        detail_card = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
        detail_card.pack(fill="x", pady=(0, 12))

        d_box = ctk.CTkFrame(detail_card, fg_color="transparent")
        d_box.pack(fill="x", padx=16, pady=12)

        # Order Number & ID
        r1 = ctk.CTkFrame(d_box, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        ctk.CTkLabel(r1, text="Order Number:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(r1, text=f"{self.order.order_number}  (ID #{self.order.id})", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=accent_col).pack(side="right")

        # Dining Table / Type
        r2 = ctk.CTkFrame(d_box, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkLabel(r2, text="Dining Mode:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(r2, text=self.order.table_number, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(side="right")

        # Current Status
        r3 = ctk.CTkFrame(d_box, fg_color="transparent")
        r3.pack(fill="x", pady=2)
        ctk.CTkLabel(r3, text="Current Status:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        st_pill = ctk.CTkFrame(r3, fg_color="#DBEAFE", corner_radius=6)
        st_pill.pack(side="right")
        ctk.CTkLabel(st_pill, text=f"● {self.order.status} (Received by Kitchen)", font=ctk.CTkFont(size=10, weight="bold"), text_color="#1D4ED8").pack(padx=8, pady=2)

        # Estimated Prep Time (reliable calculation based on quantity)
        total_qty = sum(item.quantity for item in self.order.items)
        if total_qty <= 2:
            prep_time = "10–15 Minutes"
        elif total_qty <= 5:
            prep_time = "15–20 Minutes"
        else:
            prep_time = "20–30 Minutes"

        r4 = ctk.CTkFrame(d_box, fg_color="transparent")
        r4.pack(fill="x", pady=2)
        ctk.CTkLabel(r4, text="Estimated Prep Time:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(side="left")
        ctk.CTkLabel(r4, text=f"⏱️ {prep_time}", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["warning"]).pack(side="right")

        # Ordered Items Summary
        items_card = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=10, border_width=1, border_color=border_col)
        items_card.pack(fill="x", pady=(0, 12))

        i_box = ctk.CTkFrame(items_card, fg_color="transparent")
        i_box.pack(fill="x", padx=16, pady=10)

        ctk.CTkLabel(i_box, text="Dishes Ordered:", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_sec).pack(anchor="w", pady=(0, 4))
        subtotal = Decimal("0.00")
        for item in self.order.items:
            subtotal += item.line_total
            it_r = ctk.CTkFrame(i_box, fg_color="transparent")
            it_r.pack(fill="x", pady=2)
            ctk.CTkLabel(it_r, text=f"• {item.item_name}  ×{item.quantity}", font=ctk.CTkFont(size=11), text_color=text_pri).pack(side="left")
            ctk.CTkLabel(it_r, text=f"{CURRENCY_SYMBOL}{item.line_total:.2f}", font=ctk.CTkFont(size=11, weight="bold"), text_color=text_pri).pack(side="right")

        est_gst = (subtotal * (DEFAULT_TAX_RATE / Decimal("100.00"))).quantize(Decimal("0.01"))
        net_total = (subtotal + est_gst).quantize(Decimal("0.01"))

        ctk.CTkFrame(i_box, height=1, fg_color=border_col).pack(fill="x", pady=(6, 6))

        tot_r = ctk.CTkFrame(i_box, fg_color="transparent")
        tot_r.pack(fill="x", pady=2)
        ctk.CTkLabel(tot_r, text="Total Amount (Incl. GST):", font=ctk.CTkFont(size=12, weight="bold"), text_color=text_pri).pack(side="left")
        ctk.CTkLabel(tot_r, text=f"{CURRENCY_SYMBOL}{net_total:.2f}", font=ctk.CTkFont(size=15, weight="bold"), text_color=palette["success"]).pack(side="right")

        # Payment settlement instruction
        settle_box = ctk.CTkFrame(scroll, fg_color=card_col, corner_radius=8, border_width=1, border_color=border_col)
        settle_box.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            settle_box,
            text="💳 Payment at Counter",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=accent_col
        ).pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            settle_box,
            text=f"Please provide Order #{self.order.order_number} to the cashier when making payment at the counter.",
            font=ctk.CTkFont(size=10),
            text_color=text_sec,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Bottom Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_bar,
            text="Close",
            width=100,
            height=38,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=card_col,
            text_color=text_pri,
            border_width=1,
            border_color=border_col,
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_bar,
            text="⚡ Track My Order",
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=accent_col,
            hover_color=hover_col,
            text_color="#FFFFFF",
            command=self._handle_track
        ).pack(side="right", fill="x", expand=True, padx=(12, 0))

    def _handle_track(self):
        order_id = self.order.id
        self.destroy()
        if self.on_track_order:
            self.on_track_order(order_id)
