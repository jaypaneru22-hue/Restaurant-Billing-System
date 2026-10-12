"""Order creation and order history views for high-efficiency cashier point-of-sale."""
import customtkinter as ctk
from decimal import Decimal
from typing import Callable, Optional, Dict, List
from services.order_service import OrderService, order_service
from services.menu_service import MenuService, menu_service
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_CATEGORIES, CURRENCY_SYMBOL


class NewOrderFrame(ctk.CTkFrame):
    """Point-of-Sale Order creation view with fast dish catalog and live cart."""

    def __init__(
        self,
        master,
        on_proceed_to_bill: Callable[[int], None],
        order_svc: OrderService = order_service,
        menu_svc: MenuService = menu_service,
        auth_svc: AuthService = auth_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_proceed_to_bill = on_proceed_to_bill
        self.order_svc = order_svc
        self.menu_svc = menu_svc
        self.auth_svc = auth_svc

        # Cart: {menu_item_id: {"name": str, "price": Decimal, "qty": int}}
        self.cart: Dict[int, Dict] = {}

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_catalog()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_catalog()
            self._render_cart()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Main 2-column split (Left: Catalog, Right: Cart)
        self.grid_columnconfigure(0, weight=3, uniform="order_split")
        self.grid_columnconfigure(1, weight=2, uniform="order_split")
        self.grid_rowconfigure(0, weight=1)

        # ----------------- LEFT: DISH CATALOG -----------------
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=15)

        # Catalog header
        cat_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        cat_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            cat_header,
            text="🍽️ Select Menu Items",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        # Search & Category Filters
        filter_bar = ctk.CTkFrame(left_panel, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        filter_bar.pack(fill="x", pady=(0, 10))

        self.entry_search = ctk.CTkEntry(filter_bar, placeholder_text="Search dishes...", width=180, height=32)
        self.entry_search.pack(side="left", padx=10, pady=8)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_catalog())

        self.combo_cat = ctk.CTkComboBox(filter_bar, values=["All"] + DEFAULT_CATEGORIES, width=150, height=32, command=lambda v: self.refresh_catalog())
        self.combo_cat.set("All")
        self.combo_cat.pack(side="left", padx=5, pady=8)

        # Scrollable catalog
        self.catalog_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.catalog_scroll.pack(fill="both", expand=True)

        # ----------------- RIGHT: ORDER CART & DETAILS -----------------
        right_panel = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=15)

        # Cart Header
        cart_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        cart_header.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(
            cart_header,
            text="🛒 Current Order",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        ctk.CTkButton(
            cart_header,
            text="Clear",
            width=50,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=palette["bg_secondary"],
            text_color=palette["danger"],
            command=self._clear_cart
        ).pack(side="right")

        # Table & Customer Fields
        meta_box = ctk.CTkFrame(right_panel, fg_color=palette["bg_secondary"], corner_radius=8)
        meta_box.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(meta_box, text="Table No:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))
        self.entry_table = ctk.CTkEntry(meta_box, height=28, width=120)
        self.entry_table.grid(row=0, column=1, padx=5, pady=(6, 2), sticky="w")
        self.entry_table.insert(0, "Table 1")

        ctk.CTkLabel(meta_box, text="Customer:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["text_secondary"]).grid(row=1, column=0, sticky="w", padx=10, pady=(2, 6))
        self.entry_customer = ctk.CTkEntry(meta_box, height=28, width=160)
        self.entry_customer.grid(row=1, column=1, padx=5, pady=(2, 6), sticky="w")
        self.entry_customer.insert(0, "Walk-in Guest")

        # Cart Items Scrollable Frame
        self.cart_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.cart_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Bottom Totals & Actions Box
        bottom_box = ctk.CTkFrame(right_panel, fg_color=palette["bg_secondary"], corner_radius=10)
        bottom_box.pack(fill="x", padx=15, pady=(0, 15))

        tot_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        tot_row.pack(fill="x", padx=15, pady=(12, 6))
        ctk.CTkLabel(tot_row, text="Order Subtotal:", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette["text_secondary"]).pack(side="left")
        self.lbl_subtotal = ctk.CTkLabel(tot_row, text=f"{CURRENCY_SYMBOL}0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=palette["success"])
        self.lbl_subtotal.pack(side="right")

        self.lbl_order_error = ctk.CTkLabel(bottom_box, text="", font=ctk.CTkFont(size=11), text_color=palette["danger"])
        self.lbl_order_error.pack(fill="x", padx=15, pady=(0, 4))

        # Action Buttons
        btn_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))

        self.btn_save_pending = ctk.CTkButton(
            btn_row,
            text="Save Pending",
            height=36,
            font=ctk.CTkFont(size=12),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=self._handle_save_pending
        )
        self.btn_save_pending.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_bill = ctk.CTkButton(
            btn_row,
            text="Proceed to Bill 💳",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_proceed_bill
        )
        self.btn_bill.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def refresh_catalog(self):
        query = self.entry_search.get().strip() if hasattr(self, "entry_search") else ""
        category = self.combo_cat.get() if hasattr(self, "combo_cat") else "All"
        items = self.menu_svc.search_items(query=query, category=category, available_only=True)
        palette = theme_manager.get_palette()

        for child in self.catalog_scroll.winfo_children():
            child.destroy()

        if not items:
            ctk.CTkLabel(self.catalog_scroll, text="No items found in catalog.", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(pady=30)
            return

        for item in items:
            card = ctk.CTkFrame(self.catalog_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.pack(fill="x", pady=4, padx=2)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=12, pady=10)

            ctk.CTkLabel(left, text=item.name, font=ctk.CTkFont(size=13, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{item.category} • {CURRENCY_SYMBOL}{item.price}", font=ctk.CTkFont(size=11), text_color=palette["text_secondary"]).pack(anchor="w")

            add_btn = ctk.CTkButton(
                card,
                text="➕ Add",
                width=70,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"],
                hover_color=palette["accent_hover"],
                command=lambda it=item: self._add_to_cart(it)
            )
            add_btn.pack(side="right", padx=12, pady=10)

    def _add_to_cart(self, item):
        if item.id in self.cart:
            self.cart[item.id]["qty"] += 1
        else:
            self.cart[item.id] = {
                "name": item.name,
                "price": item.price,
                "qty": 1
            }
        self._render_cart()

    def _render_cart(self):
        palette = theme_manager.get_palette()
        for child in self.cart_scroll.winfo_children():
            child.destroy()

        if not self.cart:
            ctk.CTkLabel(self.cart_scroll, text="No items in order yet.\nSelect items from the menu.", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).pack(pady=40)
            self.lbl_subtotal.configure(text=f"{CURRENCY_SYMBOL}0.00")
            return

        subtotal = Decimal("0.00")
        for item_id, data in self.cart.items():
            line_tot = (data["price"] * data["qty"]).quantize(Decimal("0.01"))
            subtotal += line_tot

            row = ctk.CTkFrame(self.cart_scroll, fg_color=palette["bg_secondary"], corner_radius=8)
            row.pack(fill="x", pady=3)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(left, text=data["name"][:18], font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{CURRENCY_SYMBOL}{data['price']} ea", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=8, pady=6)

            # - button
            btn_minus = ctk.CTkButton(
                right,
                text="-",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=palette["bg_card"],
                text_color=palette["text_primary"],
                command=lambda id_=item_id: self._decrease_qty(id_)
            )
            btn_minus.pack(side="left", padx=2)

            # qty label
            ctk.CTkLabel(right, text=str(data["qty"]), width=24, font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=2)

            # + button
            btn_plus = ctk.CTkButton(
                right,
                text="+",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=palette["bg_card"],
                text_color=palette["text_primary"],
                command=lambda id_=item_id: self._increase_qty(id_)
            )
            btn_plus.pack(side="left", padx=2)

            # Line total
            ctk.CTkLabel(right, text=f"{CURRENCY_SYMBOL}{line_tot}", width=65, anchor="e", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=(5, 2))

        self.lbl_subtotal.configure(text=f"{CURRENCY_SYMBOL}{subtotal.quantize(Decimal('0.01'))}")

    def _increase_qty(self, item_id: int):
        if item_id in self.cart:
            self.cart[item_id]["qty"] += 1
            self._render_cart()

    def _decrease_qty(self, item_id: int):
        if item_id in self.cart:
            if self.cart[item_id]["qty"] > 1:
                self.cart[item_id]["qty"] -= 1
            else:
                del self.cart[item_id]
            self._render_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._render_cart()

    def _create_order_record(self) -> Optional[int]:
        if not self.cart:
            self.lbl_order_error.configure(text="Please add at least one item to the cart.")
            return None

        user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else 1
        table = self.entry_table.get().strip()
        customer = self.entry_customer.get().strip()
        item_entries = [(item_id, data["qty"]) for item_id, data in self.cart.items()]

        ok, msg, order = self.order_svc.create_order(user_id, table, customer, item_entries)
        if not ok:
            self.lbl_order_error.configure(text=msg)
            return None

        self.lbl_order_error.configure(text="")
        return order.id

    def _handle_save_pending(self):
        order_id = self._create_order_record()
        if order_id:
            self._clear_cart()
            self.lbl_order_error.configure(text=f"Order saved as PENDING.", text_color=theme_manager.get_palette()["success"])

    def _handle_proceed_bill(self):
        order_id = self._create_order_record()
        if order_id:
            self._clear_cart()
            self.on_proceed_to_bill(order_id)


class OrderHistoryFrame(ctk.CTkFrame):
    """Order History and Status view with bill settlement and receipt shortcuts."""

    def __init__(
        self,
        master,
        on_open_bill: Callable[[int], None],
        on_view_receipt: Callable[[int], None],
        order_svc: OrderService = order_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_open_bill = on_open_bill
        self.on_view_receipt = on_view_receipt
        self.order_svc = order_svc

        theme_manager.subscribe(self.on_theme_changed)
        self._build_ui()
        self.refresh_history()

    def on_theme_changed(self, theme_name: str):
        if self.winfo_exists():
            palette = theme_manager.get_palette()
            self.configure(fg_color=palette["bg_primary"])
            self.refresh_history()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 15))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")
        ctk.CTkLabel(
            title_box,
            text="📜 Order History & Invoices",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_box,
            text="Audit past orders, transition pending tickets to billing, and reprint receipts",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Status filter tabs
        self.status_seg = ctk.CTkSegmentedButton(
            header,
            values=["All", "PENDING", "COMPLETED", "CANCELLED"],
            command=lambda v: self.refresh_history()
        )
        self.status_seg.set("All")
        self.status_seg.pack(side="right")

        # Scrollable table
        self.scroll_orders = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_orders.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def refresh_history(self):
        filter_status = self.status_seg.get()
        status_param = None if filter_status == "All" else filter_status
        orders = self.order_svc.list_orders(status=status_param, limit=50)
        palette = theme_manager.get_palette()

        for child in self.scroll_orders.winfo_children():
            child.destroy()

        if not orders:
            ctk.CTkLabel(self.scroll_orders, text="No orders match the selected filter.", font=ctk.CTkFont(size=13), text_color=palette["text_secondary"]).pack(pady=40)
            return

        for order in orders:
            card = ctk.CTkFrame(self.scroll_orders, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.pack(fill="x", pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)

            ctk.CTkLabel(
                left,
                text=f"{order.order_number}  •  {order.customer_name} ({order.table_number})",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(anchor="w")

            item_summary = ", ".join([f"{it.item_name} (x{it.quantity})" for it in order.items[:3]])
            if len(order.items) > 3:
                item_summary += f", +{len(order.items)-3} more"
            ctk.CTkLabel(
                left,
                text=f"{item_summary}  |  {order.created_at or ''}",
                font=ctk.CTkFont(size=11),
                text_color=palette["text_secondary"]
            ).pack(anchor="w")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=15, pady=10)

            # Status pill
            status_color = palette["success"] if order.status == "COMPLETED" else (
                palette["warning"] if order.status == "PENDING" else palette["danger"]
            )
            ctk.CTkLabel(
                right,
                text=order.status,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=status_color
            ).pack(side="left", padx=(0, 15))

            # Action button depending on status
            if order.status == "PENDING":
                bill_btn = ctk.CTkButton(
                    right,
                    text="Bill Order 💳",
                    width=90,
                    height=28,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=palette["accent"],
                    hover_color=palette["accent_hover"],
                    command=lambda oid=order.id: self.on_open_bill(oid)
                )
                bill_btn.pack(side="left", padx=4)

                cancel_btn = ctk.CTkButton(
                    right,
                    text="Cancel",
                    width=60,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    fg_color=palette["danger"],
                    hover_color="#b91c1c",
                    command=lambda oid=order.id: self._cancel_order(oid)
                )
                cancel_btn.pack(side="left", padx=4)

            elif order.status == "COMPLETED":
                rcpt_btn = ctk.CTkButton(
                    right,
                    text="View Receipt 🧾",
                    width=100,
                    height=28,
                    font=ctk.CTkFont(size=11),
                    fg_color=palette["bg_secondary"],
                    text_color=palette["text_primary"],
                    hover_color=palette["border"],
                    command=lambda oid=order.id: self.on_view_receipt(oid)
                )
                rcpt_btn.pack(side="left", padx=4)

    def _cancel_order(self, order_id: int):
        ok, msg = self.order_svc.cancel_order(order_id)
        if ok:
            self.refresh_history()
