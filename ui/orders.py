"""Order creation and order history views for high-efficiency cashier point-of-sale."""
import customtkinter as ctk
from decimal import Decimal
from typing import Callable, Optional, Dict, List
from services.order_service import OrderService, order_service
from services.menu_service import MenuService, menu_service
from services.auth_service import AuthService, auth_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_CATEGORIES, CURRENCY_SYMBOL, DEFAULT_TAX_RATE


class NewOrderFrame(ctk.CTkFrame):
    """Modern Point-of-Sale Order creation view with category pills, live cart, and fast checkout."""

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
        self.selected_category: str = "All"

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

        # Main 2-column split (Left: Dish Catalog 60%, Right: Order Cart 40%)
        self.grid_columnconfigure(0, weight=3, uniform="order_split")
        self.grid_columnconfigure(1, weight=2, uniform="order_split")
        self.grid_rowconfigure(0, weight=1)

        # =========================================================================
        # LEFT PANEL: MENU CATALOG & SEARCH
        # =========================================================================
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=16)

        # Header Title
        cat_header = ctk.CTkFrame(left_panel, fg_color="transparent")
        cat_header.pack(fill="x", pady=(0, 10))

        title_col = ctk.CTkFrame(cat_header, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="🍽️ Point of Sale — Menu Catalog",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text="Select dishes or use search to add items to active order",
            font=ctk.CTkFont(size=11),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Search Bar
        search_card = ctk.CTkFrame(left_panel, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
        search_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(search_card, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(12, 4))
        self.entry_search = ctk.CTkEntry(
            search_card,
            placeholder_text="Search menu dishes by name...",
            height=34,
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=12)
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_catalog())

        btn_clear_search = ctk.CTkButton(
            search_card,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=palette["bg_secondary"],
            text_color=palette["text_secondary"],
            command=self._clear_search
        )
        btn_clear_search.pack(side="right", padx=6)

        # Category Filter Pills Bar
        cat_bar = ctk.CTkScrollableFrame(left_panel, height=44, orientation="horizontal", fg_color="transparent")
        cat_bar.pack(fill="x", pady=(0, 10))

        self.category_buttons = {}
        all_cats = ["All"] + DEFAULT_CATEGORIES
        for cat in all_cats:
            btn = ctk.CTkButton(
                cat_bar,
                text=cat,
                height=30,
                corner_radius=15,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"] if cat == self.selected_category else palette["bg_card"],
                text_color="#ffffff" if cat == self.selected_category else palette["text_primary"],
                hover_color=palette["accent_hover"],
                border_width=1,
                border_color=palette["border"],
                command=lambda c=cat: self._select_category(c)
            )
            btn.pack(side="left", padx=3)
            self.category_buttons[cat] = btn

        # Scrollable Catalog Grid/List
        self.catalog_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.catalog_scroll.pack(fill="both", expand=True)

        # =========================================================================
        # RIGHT PANEL: LIVE CART & CHECKOUT
        # =========================================================================
        right_panel = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=16)

        # Cart Header
        cart_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        cart_header.pack(fill="x", padx=16, pady=(16, 10))

        self.lbl_cart_title = ctk.CTkLabel(
            cart_header,
            text="🛒 Current Order Ticket",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        )
        self.lbl_cart_title.pack(side="left")

        ctk.CTkButton(
            cart_header,
            text="Clear Cart",
            width=70,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_secondary"],
            hover_color=palette["danger"],
            text_color=palette["text_secondary"],
            command=self._clear_cart
        ).pack(side="right")

        # Table & Customer Metadata
        meta_box = ctk.CTkFrame(right_panel, fg_color=palette["bg_secondary"], corner_radius=8, border_width=1, border_color=palette["border"])
        meta_box.pack(fill="x", padx=16, pady=(0, 10))

        # Row 1: Table Number
        t_row = ctk.CTkFrame(meta_box, fg_color="transparent")
        t_row.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(t_row, text="Table No:", width=70, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", "#334155")).pack(side="left")
        self.entry_table = ctk.CTkEntry(t_row, height=28, width=110, font=ctk.CTkFont(size=12))
        self.entry_table.pack(side="left", padx=4)
        self.entry_table.insert(0, "Table 1")

        # Quick table pills
        for t_name in ["T1", "T2", "T3", "Parcel"]:
            ctk.CTkButton(
                t_row,
                text=t_name,
                width=42,
                height=24,
                font=ctk.CTkFont(size=10),
                fg_color=palette["bg_card"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda t=t_name: self._set_table(t)
            ).pack(side="left", padx=2)

        # Row 2: Customer Name
        c_row = ctk.CTkFrame(meta_box, fg_color="transparent")
        c_row.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkLabel(c_row, text="Customer:", width=70, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", "#334155")).pack(side="left")
        self.entry_customer = ctk.CTkEntry(c_row, height=28, font=ctk.CTkFont(size=12))
        self.entry_customer.pack(side="left", fill="x", expand=True, padx=4)
        self.entry_customer.insert(0, "Walk-in Guest")

        # Cart Items Scrollable Frame
        self.cart_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.cart_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Bottom Totals & Actions Box
        bottom_box = ctk.CTkFrame(right_panel, fg_color=palette["bg_secondary"], corner_radius=10, border_width=1, border_color=palette["border"])
        bottom_box.pack(fill="x", padx=16, pady=(0, 16))

        # Financial breakdown inside cart
        calc_inner = ctk.CTkFrame(bottom_box, fg_color="transparent")
        calc_inner.pack(fill="x", padx=14, pady=(10, 4))

        sub_row = ctk.CTkFrame(calc_inner, fg_color="transparent")
        sub_row.pack(fill="x", pady=1)
        ctk.CTkLabel(sub_row, text="Items Subtotal:", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", "#334155")).pack(side="left")
        self.lbl_subtotal = ctk.CTkLabel(sub_row, text=f"{CURRENCY_SYMBOL}0.00", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"])
        self.lbl_subtotal.pack(side="right")

        tax_row = ctk.CTkFrame(calc_inner, fg_color="transparent")
        tax_row.pack(fill="x", pady=1)
        ctk.CTkLabel(tax_row, text="Estimated GST (5%):", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", "#334155")).pack(side="left")
        self.lbl_est_tax = ctk.CTkLabel(tax_row, text=f"{CURRENCY_SYMBOL}0.00", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"])
        self.lbl_est_tax.pack(side="right")

        tot_row = ctk.CTkFrame(calc_inner, fg_color="transparent")
        tot_row.pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(tot_row, text="Estimated Net Total:", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette["text_primary"]).pack(side="left")
        self.lbl_grand_total = ctk.CTkLabel(tot_row, text=f"{CURRENCY_SYMBOL}0.00", font=ctk.CTkFont(size=18, weight="bold"), text_color=palette["success"])
        self.lbl_grand_total.pack(side="right")

        self.lbl_order_error = ctk.CTkLabel(bottom_box, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette["danger"])
        self.lbl_order_error.pack(fill="x", padx=14, pady=(0, 4))

        # Action Buttons
        btn_row = ctk.CTkFrame(bottom_box, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(2, 12))

        self.btn_save_pending = ctk.CTkButton(
            btn_row,
            text="Save Pending ⏳",
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            state="disabled",
            command=self._handle_save_pending
        )
        self.btn_save_pending.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_bill = ctk.CTkButton(
            btn_row,
            text="Proceed to Payment 💳",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            state="disabled",
            command=self._handle_proceed_bill
        )
        self.btn_bill.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def _set_table(self, table_str: str):
        self.entry_table.delete(0, "end")
        self.entry_table.insert(0, table_str)

    def _select_category(self, cat: str):
        self.selected_category = cat
        palette = theme_manager.get_palette()
        for c, btn in self.category_buttons.items():
            if c == cat:
                btn.configure(fg_color=palette["accent"], text_color="#ffffff")
            else:
                btn.configure(fg_color=palette["bg_card"], text_color=palette["text_primary"])
        self.refresh_catalog()

    def _clear_search(self):
        self.entry_search.delete(0, "end")
        self.refresh_catalog()

    def refresh_catalog(self):
        query = self.entry_search.get().strip() if hasattr(self, "entry_search") else ""
        category = self.selected_category if hasattr(self, "selected_category") else "All"
        items = self.menu_svc.search_items(query=query, category=category, available_only=True)
        palette = theme_manager.get_palette()

        for child in self.catalog_scroll.winfo_children():
            child.destroy()

        if not items:
            empty_frame = ctk.CTkFrame(self.catalog_scroll, fg_color="transparent")
            empty_frame.pack(pady=40)
            ctk.CTkLabel(empty_frame, text="🔍 No dishes match the current filter or search.", font=ctk.CTkFont(size=13), text_color=palette["text_secondary"]).pack()
            ctk.CTkButton(empty_frame, text="Reset Filters", height=28, fg_color=palette["bg_card"], hover_color=palette["border"], text_color=palette["text_primary"], command=self._reset_filters).pack(pady=8)
            return

        for item in items:
            card = ctk.CTkFrame(self.catalog_scroll, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.pack(fill="x", pady=3, padx=2)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=12, pady=8)

            name_row = ctk.CTkFrame(left, fg_color="transparent")
            name_row.pack(anchor="w")

            ctk.CTkLabel(name_row, text=item.name, font=ctk.CTkFont(size=13, weight="bold"), text_color=palette["text_primary"]).pack(side="left")

            # In cart badge
            if item.id in self.cart:
                in_cart_qty = self.cart[item.id]["qty"]
                badge = ctk.CTkFrame(name_row, fg_color=palette["accent"], corner_radius=10)
                badge.pack(side="left", padx=8)
                ctk.CTkLabel(badge, text=f"{in_cart_qty} in cart", font=ctk.CTkFont(size=9, weight="bold"), text_color="#ffffff").pack(padx=6, pady=1)

            # Details row (category tag + price)
            sub_row = ctk.CTkFrame(left, fg_color="transparent")
            sub_row.pack(anchor="w", pady=(2, 0))

            cat_tag = ctk.CTkFrame(sub_row, fg_color=palette["bg_secondary"], corner_radius=4)
            cat_tag.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(cat_tag, text=item.category, font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(padx=6, pady=1)

            ctk.CTkLabel(sub_row, text=f"{CURRENCY_SYMBOL}{item.price}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["success"]).pack(side="left")

            # Add button
            add_btn = ctk.CTkButton(
                card,
                text="➕ Add",
                width=75,
                height=30,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=palette["accent"],
                hover_color=palette["accent_hover"],
                command=lambda it=item: self._add_to_cart(it)
            )
            add_btn.pack(side="right", padx=12, pady=8)

    def _reset_filters(self):
        self.entry_search.delete(0, "end")
        self._select_category("All")

    def _add_to_cart(self, item):
        if item.id in self.cart:
            self.cart[item.id]["qty"] += 1
        else:
            self.cart[item.id] = {
                "name": item.name,
                "price": item.price,
                "qty": 1
            }
        self.refresh_catalog()
        self._render_cart()

    def _render_cart(self):
        palette = theme_manager.get_palette()
        for child in self.cart_scroll.winfo_children():
            child.destroy()

        total_items = sum(d["qty"] for d in self.cart.values())
        self.lbl_cart_title.configure(text=f"🛒 Order Ticket ({total_items} items)")

        if not self.cart:
            self.btn_bill.configure(state="disabled")
            self.btn_save_pending.configure(state="disabled")
            empty_box = ctk.CTkFrame(self.cart_scroll, fg_color="transparent")
            empty_box.pack(pady=40)
            ctk.CTkLabel(
                empty_box,
                text="Order ticket is empty.\nClick ➕ Add on any dish to begin.",
                font=ctk.CTkFont(size=12),
                text_color=palette["text_secondary"],
                justify="center"
            ).pack()
            self.lbl_subtotal.configure(text=f"{CURRENCY_SYMBOL}0.00")
            self.lbl_est_tax.configure(text=f"{CURRENCY_SYMBOL}0.00")
            self.lbl_grand_total.configure(text=f"{CURRENCY_SYMBOL}0.00")
            return

        self.btn_bill.configure(state="normal")
        self.btn_save_pending.configure(state="normal")

        subtotal = Decimal("0.00")
        for item_id, data in self.cart.items():
            line_tot = (data["price"] * data["qty"]).quantize(Decimal("0.01"))
            subtotal += line_tot

            row = ctk.CTkFrame(self.cart_scroll, fg_color=palette["bg_secondary"], corner_radius=8, border_width=1, border_color=palette["border"])
            row.pack(fill="x", pady=3)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(left, text=data["name"][:18], font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{CURRENCY_SYMBOL}{data['price']} each", font=ctk.CTkFont(size=10), text_color=palette["text_secondary"]).pack(anchor="w")

            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="right", padx=8, pady=6)

            # - button
            ctk.CTkButton(
                right,
                text="-",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=palette["bg_card"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda id_=item_id: self._decrease_qty(id_)
            ).pack(side="left", padx=1)

            # qty label
            ctk.CTkLabel(right, text=str(data["qty"]), width=26, font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=1)

            # + button
            ctk.CTkButton(
                right,
                text="+",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=palette["bg_card"],
                hover_color=palette["border"],
                text_color=palette["text_primary"],
                command=lambda id_=item_id: self._increase_qty(id_)
            ).pack(side="left", padx=1)

            # Line total
            ctk.CTkLabel(right, text=f"{CURRENCY_SYMBOL}{line_tot}", width=62, anchor="e", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="left", padx=(4, 2))

            # Delete button
            ctk.CTkButton(
                right,
                text="✕",
                width=22,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                hover_color=palette["danger"],
                text_color=palette["text_secondary"],
                command=lambda id_=item_id: self._remove_item(id_)
            ).pack(side="left", padx=2)

        est_tax = (subtotal * (DEFAULT_TAX_RATE / Decimal("100.00"))).quantize(Decimal("0.01"))
        grand_total = (subtotal + est_tax).quantize(Decimal("0.01"))

        self.lbl_subtotal.configure(text=f"{CURRENCY_SYMBOL}{subtotal.quantize(Decimal('0.01'))}")
        self.lbl_est_tax.configure(text=f"+{CURRENCY_SYMBOL}{est_tax}")
        self.lbl_grand_total.configure(text=f"{CURRENCY_SYMBOL}{grand_total}")

    def _increase_qty(self, item_id: int):
        if item_id in self.cart:
            self.cart[item_id]["qty"] += 1
            self.refresh_catalog()
            self._render_cart()

    def _decrease_qty(self, item_id: int):
        if item_id in self.cart:
            if self.cart[item_id]["qty"] > 1:
                self.cart[item_id]["qty"] -= 1
            else:
                del self.cart[item_id]
            self.refresh_catalog()
            self._render_cart()

    def _remove_item(self, item_id: int):
        if item_id in self.cart:
            del self.cart[item_id]
            self.refresh_catalog()
            self._render_cart()

    def _clear_cart(self):
        self.cart.clear()
        self.refresh_catalog()
        self._render_cart()

    def _create_order_record(self) -> Optional[int]:
        palette = theme_manager.get_palette()
        if not self.cart:
            self.lbl_order_error.configure(text="Please add at least one item before proceeding.", text_color=palette["danger"])
            return None

        user_id = self.auth_svc.current_user.id if self.auth_svc.current_user else 1
        table = self.entry_table.get().strip() or "Table 1"
        customer = self.entry_customer.get().strip() or "Walk-in Guest"
        item_entries = [(item_id, data["qty"]) for item_id, data in self.cart.items()]

        ok, msg, order = self.order_svc.create_order(user_id, table, customer, item_entries)
        if not ok:
            self.lbl_order_error.configure(text=msg, text_color=palette["danger"])
            return None

        self.lbl_order_error.configure(text="")
        return order.id

    def _handle_save_pending(self):
        palette = theme_manager.get_palette()
        if not self.cart:
            self.lbl_order_error.configure(text="Please add at least one item before proceeding.", text_color=palette["danger"])
            return
        order_id = self._create_order_record()
        if order_id:
            self._clear_cart()
            self.lbl_order_error.configure(text="✓ Order saved as PENDING ticket.", text_color=palette["success"])

    def _handle_proceed_bill(self):
        palette = theme_manager.get_palette()
        if not self.cart:
            self.lbl_order_error.configure(text="Please add at least one item before proceeding.", text_color=palette["danger"])
            return
        order_id = self._create_order_record()
        if order_id:
            self._clear_cart()
            self.on_proceed_to_bill(order_id)


class OrderHistoryFrame(ctk.CTkFrame):
    """Modern Order History, Status Tracking, and Invoice reprint management."""

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
            text="📜 Orders History & Billing Invoices",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Audit past orders, settle pending tickets, and reprint customer tax receipts",
            font=ctk.CTkFont(size=12),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Status filter tabs
        controls_box = ctk.CTkFrame(header, fg_color="transparent")
        controls_box.pack(side="right")

        self.status_seg = ctk.CTkSegmentedButton(
            controls_box,
            values=["All", "PENDING", "COMPLETED", "CANCELLED"],
            command=lambda v: self.refresh_history(),
            height=32,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.status_seg.set("All")
        self.status_seg.pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(
            controls_box,
            text="🔄 Refresh",
            width=90,
            height=32,
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self.refresh_history
        )
        refresh_btn.pack(side="left", padx=5)

        # Scrollable table
        self.scroll_orders = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_orders.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def refresh_history(self):
        filter_status = self.status_seg.get()
        status_param = None if filter_status == "All" else filter_status
        orders = self.order_svc.list_orders(status=status_param, limit=60)
        palette = theme_manager.get_palette()

        for child in self.scroll_orders.winfo_children():
            child.destroy()

        if not orders:
            empty_box = ctk.CTkFrame(self.scroll_orders, fg_color="transparent")
            empty_box.pack(pady=50)
            ctk.CTkLabel(
                empty_box,
                text="No orders match the selected filter status.",
                font=ctk.CTkFont(size=13),
                text_color=palette["text_secondary"]
            ).pack()
            return

        for order in orders:
            card = ctk.CTkFrame(self.scroll_orders, fg_color=palette["bg_card"], corner_radius=10, border_width=1, border_color=palette["border"])
            card.pack(fill="x", pady=4)

            # Left Details
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", padx=16, pady=12)

            title_row = ctk.CTkFrame(left, fg_color="transparent")
            title_row.pack(anchor="w")

            ctk.CTkLabel(
                title_row,
                text=order.order_number,
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(side="left")

            ctk.CTkLabel(
                title_row,
                text=f"  •  {order.customer_name}  ({order.table_number})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=palette["text_primary"]
            ).pack(side="left")

            # Items summary & total
            subtotal = sum((it.line_total for it in order.items), Decimal("0.00"))
            item_summary = ", ".join([f"{it.item_name} ×{it.quantity}" for it in order.items[:3]])
            if len(order.items) > 3:
                item_summary += f", +{len(order.items)-3} more"

            ctk.CTkLabel(
                left,
                text=f"{item_summary}  |  Subtotal: {CURRENCY_SYMBOL}{subtotal}  |  {order.created_at or ''}",
                font=ctk.CTkFont(size=11),
                text_color=palette["text_secondary"]
            ).pack(anchor="w", pady=(2, 0))

            # Right Status & Action buttons
            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=16, pady=12)

            # Status pill
            status_color = palette["success"] if order.status == "COMPLETED" else (
                palette["warning"] if order.status == "PENDING" else palette["danger"]
            )
            badge_bg = palette["bg_secondary"]
            status_badge = ctk.CTkFrame(right, fg_color=badge_bg, corner_radius=6, border_width=1, border_color=status_color)
            status_badge.pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                status_badge,
                text=f"● {order.status}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=status_color
            ).pack(padx=8, pady=3)

            # Actions based on status
            if order.status == "PENDING":
                bill_btn = ctk.CTkButton(
                    right,
                    text="Settle Bill 💳",
                    width=95,
                    height=30,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=palette["accent"],
                    hover_color=palette["accent_hover"],
                    command=lambda oid=order.id: self.on_open_bill(oid)
                )
                bill_btn.pack(side="left", padx=3)

                cancel_btn = ctk.CTkButton(
                    right,
                    text="Cancel",
                    width=65,
                    height=30,
                    font=ctk.CTkFont(size=11),
                    fg_color=palette["danger"],
                    hover_color="#b91c1c",
                    command=lambda oid=order.id: self._cancel_order(oid)
                )
                cancel_btn.pack(side="left", padx=3)

            elif order.status == "COMPLETED":
                rcpt_btn = ctk.CTkButton(
                    right,
                    text="View Receipt 🧾",
                    width=110,
                    height=30,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    fg_color=palette["bg_secondary"],
                    text_color=palette["text_primary"],
                    hover_color=palette["border"],
                    command=lambda oid=order.id: self.on_view_receipt(oid)
                )
                rcpt_btn.pack(side="left", padx=3)

    def _cancel_order(self, order_id: int):
        ok, msg = self.order_svc.cancel_order(order_id)
        if ok:
            self.refresh_history()
