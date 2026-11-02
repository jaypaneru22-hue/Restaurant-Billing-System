"""Billing settlement dialog and printable receipt viewer with simulated POS payments."""
import customtkinter as ctk
from decimal import Decimal, InvalidOperation
from typing import Callable, Optional
from services.billing_service import BillingService, billing_service
from services.order_service import OrderService, order_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_TAX_RATE, CURRENCY_SYMBOL, SUPPORTED_PAYMENT_METHODS
from utils.validators import validate_cash_tendered, validate_demo_card, validate_demo_upi
from utils.window_utils import center_dialog


class ReceiptDialog(ctk.CTkToplevel):
    """Itemized printable receipt viewer with thermal receipt formatting and print/export support."""

    def __init__(self, master, receipt_text: str, bill_number: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.receipt_text = receipt_text
        self.bill_number = bill_number
        self.master_ref = master
        self._last_saved_path = None
        self.billing_svc = billing_service

        self.title("Customer Invoice & Receipt")
        self.resizable(True, True)
        center_dialog(self, master, target_width=520, target_height=530, min_width=460, min_height=450)
        self.grab_set()

        self._build_ui()

    def _extract_bill_number(self) -> str:
        if self.bill_number:
            return self.bill_number
        for line in self.receipt_text.splitlines():
            if "Bill No:" in line:
                return line.split("Bill No:")[1].strip()
            if "Order No:" in line:
                return line.split("Order No:")[1].strip()
        return "RECEIPT"

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # 1. Fixed Bottom Action Bar (Packed FIRST so it is never pushed off-screen)
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(side="bottom", fill="x", padx=16, pady=(6, 12))

        # Print Receipt Button
        self.btn_print = ctk.CTkButton(
            btn_box,
            text="🖨️ Print Receipt",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            text_color="#FFFFFF",
            command=self._handle_print_receipt
        )
        self.btn_print.pack(side="left")

        # Open Saved Receipt Button (displayed if saved to disk)
        self.btn_open_file = ctk.CTkButton(
            btn_box,
            text="📂 Open File",
            height=34,
            width=90,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self._open_saved_receipt_file
        )

        self.lbl_print_status = ctk.CTkLabel(
            btn_box,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["success"],
            wraplength=230,
            justify="left"
        )
        self.lbl_print_status.pack(side="left", padx=10)

        self.btn_close = ctk.CTkButton(
            btn_box,
            text="Close (Esc)",
            width=100,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["text_primary"],
            command=self.destroy
        )
        self.btn_close.pack(side="right")

        # 2. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header,
            text="🧾 Final Receipt & Tax Invoice",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(side="left")

        # 3. Monospace textbox for receipt
        text_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            border_width=1,
            border_color=palette["border"],
            corner_radius=8
        )
        text_box.pack(side="top", fill="both", expand=True, padx=16, pady=(0, 8))
        text_box.insert("1.0", self.receipt_text)
        text_box.configure(state="disabled")

        self.bind("<Escape>", lambda e: self.destroy())

    def _handle_print_receipt(self):
        palette = theme_manager.get_palette()
        bill_num = self._extract_bill_number()
        ok, msg, file_path = self.billing_svc.print_receipt(self.receipt_text, bill_num)
        self._last_saved_path = file_path
        if ok:
            self.lbl_print_status.configure(
                text="✓ Sent to printer",
                text_color=palette["success"]
            )
            if file_path and file_path.exists():
                self.btn_open_file.pack(side="left", padx=4)
        else:
            self.lbl_print_status.configure(
                text="⚠️ Printer unavailable (File saved)",
                text_color=palette["warning"]
            )
            if file_path and file_path.exists():
                self.btn_open_file.pack(side="left", padx=4)

    def _open_saved_receipt_file(self):
        if self._last_saved_path and self._last_saved_path.exists():
            import sys
            import os
            try:
                if sys.platform == "win32":
                    os.startfile(str(self._last_saved_path))
                else:
                    import subprocess
                    subprocess.run(["xdg-open", str(self._last_saved_path)], check=False)
            except Exception as e:
                self.lbl_print_status.configure(text=f"Error: {e}")


class BillingDialog(ctk.CTkToplevel):
    """Modern POS settlement dialog with live Cash/Card/UPI simulation and guaranteed button visibility."""

    def __init__(
        self,
        master,
        order_id: int,
        on_bill_completed: Callable[[int], None],
        billing_svc: BillingService = billing_service,
        order_svc: OrderService = order_service,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.order_id = order_id
        self.on_bill_completed = on_bill_completed
        self.billing_svc = billing_svc
        self.order_svc = order_svc

        self.order = self.order_svc.get_order(order_id)
        if not self.order:
            self.destroy()
            return

        self.title(f"POS Settlement — {self.order.order_number}")
        self.resizable(True, True)
        center_dialog(self, master, target_width=600, target_height=490, min_width=520, min_height=440)
        self.grab_set()

        self._current_breakdown = {}
        self._is_submitting = False

        self._build_ui()
        self._recalculate()
        self._switch_payment_view("CASH")

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # -------------------------------------------------------------
        # 1. FIXED BOTTOM ACTION BAR
        # Packed FIRST with side="bottom" to guarantee it is NEVER pushed off screen
        # -------------------------------------------------------------
        bottom_container = ctk.CTkFrame(self, fg_color=palette["bg_secondary"], corner_radius=0, border_width=1, border_color=palette["border"])
        bottom_container.pack(side="bottom", fill="x")

        # Error notification strip
        self.lbl_error = ctk.CTkLabel(
            bottom_container,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["danger"],
            wraplength=580
        )
        self.lbl_error.pack(fill="x", padx=16, pady=(2, 2))

        btn_bar = ctk.CTkFrame(bottom_container, fg_color="transparent")
        btn_bar.pack(fill="x", padx=16, pady=(2, 10))

        self.btn_cancel = ctk.CTkButton(
            btn_bar,
            text="✕ Cancel Payment (Esc)",
            width=130,
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["border"],
            command=self._handle_cancel
        )
        self.btn_cancel.pack(side="left")

        self.btn_split = ctk.CTkButton(
            btn_bar,
            text="✂️ Split Bill",
            width=110,
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=palette.get("accent_secondary", palette["accent"]),
            hover_color=palette["accent_hover"],
            command=self._handle_split_bill
        )
        self.btn_split.pack(side="left", padx=(8, 0))

        self.btn_confirm = ctk.CTkButton(
            btn_bar,
            text="Confirm Payment & Settle Bill 💳",
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_finalize
        )
        self.btn_confirm.pack(side="right")

        # -------------------------------------------------------------
        # 2. COMPACT TOP HEADER
        # -------------------------------------------------------------
        header = ctk.CTkFrame(self, fg_color=palette["bg_secondary"], height=46, corner_radius=0, border_width=1, border_color=palette["border"])
        header.pack(side="top", fill="x")

        hdr_inner = ctk.CTkFrame(header, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=16, pady=6)

        title_col = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col,
            text=f"💳 Settle Bill: {self.order.order_number}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w")

        info_text = f"Table: {self.order.table_number}  •  Guest: {self.order.customer_name}  •  Items: {len(self.order.items)}"
        ctk.CTkLabel(
            title_col,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color=palette["text_secondary"]
        ).pack(anchor="w")

        # Status badge
        badge = ctk.CTkFrame(hdr_inner, fg_color=palette["warning"], corner_radius=6)
        badge.pack(side="right", padx=(8, 0))
        ctk.CTkLabel(badge, text="PENDING SETTLEMENT", font=ctk.CTkFont(size=9, weight="bold"), text_color="#1a1a24").pack(padx=6, pady=2)

        # -------------------------------------------------------------
        # 3. SCROLLABLE MIDDLE CONTAINER
        # -------------------------------------------------------------
        self.scroll_body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_body.pack(side="top", fill="both", expand=True, padx=14, pady=6)

        # Row 1: Split 2-Column (Left: Items list, Right: Calculation & Totals)
        top_split = ctk.CTkFrame(self.scroll_body, fg_color="transparent")
        top_split.pack(fill="x", pady=(0, 6))
        top_split.grid_columnconfigure((0, 1), weight=1, uniform="billing_cards")

        # CARD A: Order Items Summary
        card_items = ctk.CTkFrame(top_split, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        card_items.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        ctk.CTkLabel(
            card_items,
            text=f"1. Order Items ({len(self.order.items)})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("heading", palette["text_primary"])
        ).pack(anchor="w", padx=10, pady=(6, 2))

        items_scroll = ctk.CTkScrollableFrame(card_items, fg_color="transparent", height=90)
        items_scroll.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        for it in self.order.items:
            row = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"• {it.item_name} × {it.quantity}", font=ctk.CTkFont(size=10), text_color=palette["text_primary"]).pack(side="left")
            ctk.CTkLabel(row, text=f"{CURRENCY_SYMBOL}{it.line_total}", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette["text_primary"]).pack(side="right")

        # CARD B: Discount, GST & Financial Summary
        card_calc = ctk.CTkFrame(top_split, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        card_calc.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        ctk.CTkLabel(
            card_calc,
            text="2. Financial Breakdown",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("section_heading", palette["text_primary"])
        ).pack(anchor="w", padx=10, pady=(6, 4))

        # Inputs row
        inputs_row = ctk.CTkFrame(card_calc, fg_color="transparent")
        inputs_row.pack(fill="x", padx=10, pady=(0, 4))

        # Discount input
        d_box = ctk.CTkFrame(inputs_row, fg_color="transparent")
        d_box.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(d_box, text="Discount (%):", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).pack(anchor="w")
        self.entry_discount = ctk.CTkEntry(d_box, height=26, font=ctk.CTkFont(size=11))
        self.entry_discount.insert(0, "0")
        self.entry_discount.pack(fill="x", pady=(1, 0))
        self.entry_discount.bind("<KeyRelease>", lambda e: self._recalculate())

        # Tax input
        t_box = ctk.CTkFrame(inputs_row, fg_color="transparent")
        t_box.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(t_box, text="GST Tax (%):", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).pack(anchor="w")
        self.entry_tax = ctk.CTkEntry(t_box, height=26, font=ctk.CTkFont(size=11))
        initial_tax = self.billing_svc.get_configured_tax_rate() if hasattr(self.billing_svc, "get_configured_tax_rate") else DEFAULT_TAX_RATE
        self.entry_tax.insert(0, str(initial_tax))
        self.entry_tax.pack(fill="x", pady=(1, 0))
        self.entry_tax.bind("<KeyRelease>", lambda e: self._recalculate())

        # Net breakdown card
        sum_box = ctk.CTkFrame(card_calc, fg_color=palette["bg_secondary"], corner_radius=6)
        sum_box.pack(fill="x", padx=10, pady=(2, 6))

        self.lbl_subtotal = ctk.CTkLabel(sum_box, text="Subtotal: ₹0.00 | Disc: -₹0.00", font=ctk.CTkFont(size=10), text_color=palette.get("body", palette["text_secondary"]))
        self.lbl_subtotal.pack(anchor="w", padx=8, pady=(4, 0))

        self.lbl_tax_amt = ctk.CTkLabel(sum_box, text="GST (5%): +₹0.00", font=ctk.CTkFont(size=10), text_color=palette.get("body", palette["text_secondary"]))
        self.lbl_tax_amt.pack(anchor="w", padx=8, pady=0)

        self.lbl_final_total = ctk.CTkLabel(sum_box, text="Net Payable Total: ₹0.00", font=ctk.CTkFont(size=14, weight="bold"), text_color=palette["success"])
        self.lbl_final_total.pack(anchor="w", padx=8, pady=(1, 4))

        # CARD C: Payment Method Selector & Interactive Panel
        card_pay = ctk.CTkFrame(self.scroll_body, fg_color=palette["bg_card"], corner_radius=8, border_width=1, border_color=palette["border"])
        card_pay.pack(fill="x", pady=(0, 6))

        pay_head = ctk.CTkFrame(card_pay, fg_color="transparent")
        pay_head.pack(fill="x", padx=10, pady=(6, 4))

        ctk.CTkLabel(
            pay_head,
            text="3. Payment Method:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette.get("section_heading", palette["text_primary"])
        ).pack(side="left")

        # Segmented payment selector
        self.pay_method_var = ctk.StringVar(value="CASH")
        self.seg_payment = ctk.CTkSegmentedButton(
            pay_head,
            values=["CASH", "CARD", "UPI"],
            command=self._switch_payment_view,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.seg_payment.set("CASH")
        self.seg_payment.pack(side="right")

        # Dynamic details container
        self.details_frame = ctk.CTkFrame(card_pay, fg_color="transparent")
        self.details_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.bind("<Escape>", lambda e: self._handle_cancel())

    def _switch_payment_view(self, method: str):
        """Switches the interactive payment sub-panel between Cash, Demo Card, and Demo UPI."""
        palette = theme_manager.get_palette()
        self.pay_method_var.set(method)

        for child in self.details_frame.winfo_children():
            child.destroy()

        if method == "CASH":
            self._render_cash_panel(palette)
        elif method == "CARD":
            self._render_card_panel(palette)
        elif method == "UPI":
            self._render_upi_panel(palette)

    def _render_cash_panel(self, palette: dict):
        box = ctk.CTkFrame(self.details_frame, fg_color=palette["bg_secondary"], corner_radius=6)
        box.pack(fill="x", pady=1)

        input_row = ctk.CTkFrame(box, fg_color="transparent")
        input_row.pack(fill="x", padx=10, pady=(6, 4))

        ctk.CTkLabel(input_row, text="Tendered Cash (₹):", font=ctk.CTkFont(size=11, weight="bold"), text_color=palette.get("form_label", palette["text_primary"])).pack(side="left")
        self.entry_cash_tendered = ctk.CTkEntry(input_row, width=105, height=28, font=ctk.CTkFont(size=11, weight="bold"))
        self.entry_cash_tendered.pack(side="left", padx=8)

        # Pre-fill with exact final total
        net_tot = str(self._current_breakdown.get("final_total", "0.00"))
        self.entry_cash_tendered.insert(0, net_tot)
        self.entry_cash_tendered.bind("<KeyRelease>", lambda e: self._update_cash_change())

        # Quick tender helper buttons in same or compact row
        ctk.CTkButton(input_row, text="Exact", width=46, height=24, font=ctk.CTkFont(size=9, weight="bold"), fg_color=palette["bg_card"], hover_color=palette["border"], text_color=palette["text_primary"], command=self._fill_exact_cash).pack(side="left", padx=2)
        ctk.CTkButton(input_row, text="+₹100", width=48, height=24, font=ctk.CTkFont(size=9), fg_color=palette["bg_card"], hover_color=palette["border"], text_color=palette["text_primary"], command=lambda: self._add_cash(100)).pack(side="left", padx=2)
        ctk.CTkButton(input_row, text="+₹500", width=48, height=24, font=ctk.CTkFont(size=9), fg_color=palette["bg_card"], hover_color=palette["border"], text_color=palette["text_primary"], command=lambda: self._add_cash(500)).pack(side="left", padx=2)
        ctk.CTkButton(input_row, text="+₹1000", width=52, height=24, font=ctk.CTkFont(size=9), fg_color=palette["bg_card"], hover_color=palette["border"], text_color=palette["text_primary"], command=lambda: self._add_cash(1000)).pack(side="left", padx=2)

        # Change due display
        self.lbl_change_due = ctk.CTkLabel(box, text="Change to Return: ₹0.00", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["success"])
        self.lbl_change_due.pack(anchor="w", padx=10, pady=(2, 6))
        self._update_cash_change()

    def _render_card_panel(self, palette: dict):
        box = ctk.CTkFrame(self.details_frame, fg_color=palette["bg_secondary"], corner_radius=6)
        box.pack(fill="x", pady=1)

        # Placement / Demo Safety Notice
        notice_box = ctk.CTkFrame(box, fg_color=palette["bg_card"], corner_radius=4, border_width=1, border_color=palette["border"])
        notice_box.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(
            notice_box,
            text="🔒 DEMO SIMULATED PAYMENT (No real card details or banking data)",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=palette["accent"]
        ).pack(padx=6, pady=2)

        # Inputs Grid
        card_grid = ctk.CTkFrame(box, fg_color="transparent")
        card_grid.pack(fill="x", padx=10, pady=(0, 4))
        card_grid.grid_columnconfigure((0, 1), weight=1)

        # Cardholder name
        ctk.CTkLabel(card_grid, text="Cardholder Name:", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).grid(row=0, column=0, sticky="w", pady=(1, 0))
        self.entry_card_name = ctk.CTkEntry(card_grid, height=26, font=ctk.CTkFont(size=11))
        self.entry_card_name.insert(0, self.order.customer_name if self.order.customer_name else "Valued Guest")
        self.entry_card_name.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 2))

        # Card Number
        ctk.CTkLabel(card_grid, text="Simulated Card Number (16 digits):", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).grid(row=0, column=1, sticky="w", pady=(1, 0))
        self.entry_card_num = ctk.CTkEntry(card_grid, height=26, font=ctk.CTkFont(size=11))
        self.entry_card_num.insert(0, "4532 8812 9011 3456")
        self.entry_card_num.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 2))

        # Expiry & CVV Row
        exp_row = ctk.CTkFrame(box, fg_color="transparent")
        exp_row.pack(fill="x", padx=10, pady=(2, 6))

        ctk.CTkLabel(exp_row, text="Expiry (MM/YY):", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).pack(side="left")
        self.entry_card_exp = ctk.CTkEntry(exp_row, width=70, height=26, font=ctk.CTkFont(size=11))
        self.entry_card_exp.insert(0, "12/28")
        self.entry_card_exp.pack(side="left", padx=(4, 12))

        ctk.CTkLabel(exp_row, text="CVV:", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).pack(side="left")
        self.entry_card_cvv = ctk.CTkEntry(exp_row, width=50, height=26, font=ctk.CTkFont(size=11), show="•")
        self.entry_card_cvv.insert(0, "888")
        self.entry_card_cvv.pack(side="left", padx=(4, 12))

        # Fast Demo Fill button
        ctk.CTkButton(
            exp_row,
            text="✨ Fill Demo Card",
            height=24,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["accent"],
            command=self._fill_demo_card
        ).pack(side="right")

    def _render_upi_panel(self, palette: dict):
        box = ctk.CTkFrame(self.details_frame, fg_color=palette["bg_secondary"], corner_radius=6)
        box.pack(fill="x", pady=1)

        # Placement / Demo Safety Notice
        notice_box = ctk.CTkFrame(box, fg_color=palette["bg_card"], corner_radius=4, border_width=1, border_color=palette["border"])
        notice_box.pack(fill="x", padx=10, pady=(6, 4))
        ctk.CTkLabel(
            notice_box,
            text="📱 DEMO UPI SCAN & PAY (Simulated Sandbox Transaction)",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=palette["accent"]
        ).pack(padx=6, pady=2)

        upi_row = ctk.CTkFrame(box, fg_color="transparent")
        upi_row.pack(fill="x", padx=10, pady=(2, 4))

        ctk.CTkLabel(upi_row, text="Customer UPI ID / VPA:", font=ctk.CTkFont(size=10, weight="bold"), text_color=palette.get("form_label", palette["text_secondary"])).pack(side="left")
        self.entry_upi_id = ctk.CTkEntry(upi_row, width=200, height=26, font=ctk.CTkFont(size=11))
        self.entry_upi_id.insert(0, "guest@okaxis")
        self.entry_upi_id.pack(side="left", padx=8)

        ctk.CTkButton(
            upi_row,
            text="✨ Demo ID",
            height=24,
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=palette["bg_card"],
            hover_color=palette["border"],
            text_color=palette["accent"],
            command=lambda: (self.entry_upi_id.delete(0, "end"), self.entry_upi_id.insert(0, "restaurant.cashier@upi"))
        ).pack(side="left")

        # Mock QR Badge
        qr_badge = ctk.CTkFrame(box, fg_color=palette["bg_card"], corner_radius=6)
        qr_badge.pack(fill="x", padx=10, pady=(2, 6))
        ctk.CTkLabel(
            qr_badge,
            text="[ ☵☲☵ QR SCANNER SIMULATION ☵☲☵ ] — Google Pay • PhonePe • Paytm • BHIM UPI",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=palette["text_secondary"],
            justify="center"
        ).pack(padx=8, pady=4)

    def _fill_exact_cash(self):
        tot = str(self._current_breakdown.get("final_total", "0.00"))
        if hasattr(self, "entry_cash_tendered"):
            self.entry_cash_tendered.delete(0, "end")
            self.entry_cash_tendered.insert(0, tot)
            self._update_cash_change()

    def _add_cash(self, increment: int):
        if hasattr(self, "entry_cash_tendered"):
            val_str = self.entry_cash_tendered.get().strip() or "0"
            try:
                curr = Decimal(val_str)
            except Exception:
                curr = Decimal("0.00")
            new_val = (curr + Decimal(str(increment))).quantize(Decimal("0.01"))
            self.entry_cash_tendered.delete(0, "end")
            self.entry_cash_tendered.insert(0, str(new_val))
            self._update_cash_change()

    def _fill_demo_card(self):
        if hasattr(self, "entry_card_name"):
            self.entry_card_name.delete(0, "end")
            self.entry_card_name.insert(0, "Jay Paneru (Demo)")
        if hasattr(self, "entry_card_num"):
            self.entry_card_num.delete(0, "end")
            self.entry_card_num.insert(0, "4532 8812 9011 3456")
        if hasattr(self, "entry_card_exp"):
            self.entry_card_exp.delete(0, "end")
            self.entry_card_exp.insert(0, "12/28")
        if hasattr(self, "entry_card_cvv"):
            self.entry_card_cvv.delete(0, "end")
            self.entry_card_cvv.insert(0, "888")

    def _update_cash_change(self):
        if not hasattr(self, "entry_cash_tendered") or not hasattr(self, "lbl_change_due"):
            return
        palette = theme_manager.get_palette()
        net_total = self._current_breakdown.get("final_total", Decimal("0.00"))
        tendered_str = self.entry_cash_tendered.get().strip()
        ok, msg, tendered, change = validate_cash_tendered(tendered_str, net_total)
        if ok:
            self.lbl_change_due.configure(text=f"Change to Return: {CURRENCY_SYMBOL}{change}", text_color=palette["success"])
            self.lbl_error.configure(text="")
        else:
            self.lbl_change_due.configure(text="Insufficient Cash", text_color=palette["danger"])

    def _recalculate(self):
        subtotal = sum((it.line_total for it in self.order.items), Decimal("0.00"))
        disc_str = self.entry_discount.get().strip() or "0"
        tax_str = self.entry_tax.get().strip() or "5.0"

        try:
            disc_dec = Decimal(disc_str)
            tax_dec = Decimal(tax_str)
            breakdown = self.billing_svc.calculate_bill_breakdown(subtotal, disc_dec, tax_dec)
            self._current_breakdown = breakdown
            self.lbl_subtotal.configure(text=f"Subtotal: {CURRENCY_SYMBOL}{breakdown['subtotal']}  |  Discount: -{CURRENCY_SYMBOL}{breakdown['discount_amount']}")
            self.lbl_tax_amt.configure(text=f"GST ({breakdown['tax_rate']}%): +{CURRENCY_SYMBOL}{breakdown['tax_amount']}")
            self.lbl_final_total.configure(text=f"Net Payable Total: {CURRENCY_SYMBOL}{breakdown['final_total']}")
            self.lbl_error.configure(text="")
            if self.pay_method_var.get() == "CASH":
                self._update_cash_change()
        except Exception:
            self.lbl_error.configure(text="Invalid numeric values for discount or tax rate.")

    def _handle_cancel(self):
        """Cancels payment dialog. Order remains PENDING and no bill is created."""
        self.destroy()

    def _handle_finalize(self):
        """Validates payment method details, finalizes the bill, and launches the receipt."""
        if self._is_submitting:
            return

        disc_str = self.entry_discount.get().strip()
        tax_str = self.entry_tax.get().strip()
        pm = self.pay_method_var.get()
        net_total = self._current_breakdown.get("final_total", Decimal("0.00"))

        # Validation per payment method
        if pm == "CASH":
            tendered_str = self.entry_cash_tendered.get().strip() if hasattr(self, "entry_cash_tendered") else ""
            valid_cash, cash_msg, _, _ = validate_cash_tendered(tendered_str, net_total)
            if not valid_cash:
                self.lbl_error.configure(text=cash_msg)
                return
        elif pm == "CARD":
            c_name = self.entry_card_name.get().strip() if hasattr(self, "entry_card_name") else ""
            c_num = self.entry_card_num.get().strip() if hasattr(self, "entry_card_num") else ""
            c_exp = self.entry_card_exp.get().strip() if hasattr(self, "entry_card_exp") else ""
            c_cvv = self.entry_card_cvv.get().strip() if hasattr(self, "entry_card_cvv") else ""
            valid_card, card_msg = validate_demo_card(c_num, c_name, c_exp, c_cvv)
            if not valid_card:
                self.lbl_error.configure(text=card_msg)
                return
        elif pm == "UPI":
            upi_id = self.entry_upi_id.get().strip() if hasattr(self, "entry_upi_id") else ""
            valid_upi, upi_msg = validate_demo_upi(upi_id)
            if not valid_upi:
                self.lbl_error.configure(text=upi_msg)
                return

        # Prevent duplicate submissions
        self._is_submitting = True
        self.btn_confirm.configure(state="disabled", text="Processing Settlement...")
        self.update_idletasks()

        ok, msg, bill = self.billing_svc.finalize_bill(
            order_id=self.order.id,
            payment_method=pm,
            discount_percent_input=disc_str,
            tax_rate_input=tax_str
        )

        if not ok:
            self._is_submitting = False
            self.btn_confirm.configure(state="normal", text="Confirm Payment & Settle Bill 💳")
            self.lbl_error.configure(text=msg)
            return

        # Generate and show receipt
        receipt_text = self.billing_svc.format_receipt_text(bill, self.order)
        self.destroy()
        ReceiptDialog(self.master, receipt_text)
        self.on_bill_completed(self.order.id)

    def _handle_split_bill(self):
        """Opens equal and custom party split settlement modal."""
        from models.bill import Bill
        from ui.split_billing import SplitBillingDialog
        disc_str = self.entry_discount.get().strip() or "0"
        tax_str = self.entry_tax.get().strip() or "5.0"
        subtotal = sum((it.line_total for it in self.order.items), Decimal("0.00"))
        breakdown = self.billing_svc.calculate_bill_breakdown(
            subtotal=subtotal,
            discount_percent=disc_str,
            tax_rate=tax_str
        )
        temp_bill = Bill(
            id=0,
            bill_number=f"BILL-{self.order.order_number}",
            order_id=self.order.id,
            subtotal=breakdown["subtotal"],
            tax_rate=breakdown["tax_rate"],
            tax_amount=breakdown["tax_amount"],
            discount_percent=breakdown["discount_percent"],
            discount_amount=breakdown["discount_amount"],
            final_total=breakdown["final_total"],
            payment_method="SPLIT",
            payment_status="PAID",
            billed_at=""
        )

        def _on_split_done(shares):
            ok, msg, bill = self.billing_svc.finalize_bill(
                order_id=self.order.id,
                payment_method="SPLIT",
                discount_percent_input=disc_str,
                tax_rate_input=tax_str
            )
            if ok and bill:
                receipt_text = self.billing_svc.format_receipt_text(bill, self.order)
                self.destroy()
                ReceiptDialog(self.master, receipt_text)
                self.on_bill_completed(self.order.id)
            else:
                self.lbl_error.configure(text=msg)

        SplitBillingDialog(self, bill=temp_bill, order=self.order, on_settled=_on_split_done)
