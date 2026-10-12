"""Billing settlement dialog and printable receipt viewer."""
import customtkinter as ctk
from decimal import Decimal
from typing import Callable, Optional
from services.billing_service import BillingService, billing_service
from services.order_service import OrderService, order_service
from ui.theme_manager import theme_manager
from config.settings import DEFAULT_TAX_RATE, CURRENCY_SYMBOL, SUPPORTED_PAYMENT_METHODS


class ReceiptDialog(ctk.CTkToplevel):
    """Itemized printable receipt viewer with thermal receipt formatting and reprint support."""

    def __init__(self, master, receipt_text: str, **kwargs):
        super().__init__(master, **kwargs)
        self.receipt_text = receipt_text

        self.title("Customer Invoice & Receipt")
        self.geometry("480x560")
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="🧾 Final Receipt Preview",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(side="left")

        # Monospace textbox for receipt
        text_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            border_width=1,
            border_color=palette["border"],
            corner_radius=8
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        text_box.insert("1.0", self.receipt_text)
        text_box.configure(state="disabled")

        # Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 20))

        btn_copy = ctk.CTkButton(
            btn_box,
            text="📋 Copy to Clipboard",
            height=34,
            fg_color=palette["bg_card"],
            hover_color=palette["bg_secondary"],
            text_color=palette["text_primary"],
            command=self._copy_to_clipboard
        )
        btn_copy.pack(side="left")

        self.lbl_copied = ctk.CTkLabel(btn_box, text="", font=ctk.CTkFont(size=11), text_color=palette["success"])
        self.lbl_copied.pack(side="left", padx=10)

        btn_close = ctk.CTkButton(
            btn_box,
            text="Close (Esc)",
            width=100,
            height=34,
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self.destroy
        )
        btn_close.pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.receipt_text)
        self.lbl_copied.configure(text="Copied!")


class BillingDialog(ctk.CTkToplevel):
    """Billing settlement modal with discount, tax, payment method, and receipt generation."""

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

        self.title(f"Settle Bill — {self.order.order_number}")
        self.geometry("520x600")
        self.resizable(False, False)
        self.grab_set()

        self._build_ui()
        self._recalculate()

    def _build_ui(self):
        palette = theme_manager.get_palette()
        self.configure(fg_color=palette["bg_primary"])

        # Title
        ctk.CTkLabel(
            self,
            text="💳 Bill Settlement & Payment",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=palette["text_primary"]
        ).pack(padx=25, pady=(20, 10), anchor="w")

        # Container
        container = ctk.CTkFrame(self, fg_color=palette["bg_card"], corner_radius=12, border_width=1, border_color=palette["border"])
        container.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        # Order info
        info_box = ctk.CTkFrame(container, fg_color=palette["bg_secondary"], corner_radius=8)
        info_box.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(info_box, text=f"Order: {self.order.order_number}", font=ctk.CTkFont(size=13, weight="bold"), text_color=palette["text_primary"]).grid(row=0, column=0, sticky="w", padx=10, pady=4)
        ctk.CTkLabel(info_box, text=f"Table: {self.order.table_number}", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).grid(row=0, column=1, sticky="w", padx=10, pady=4)
        ctk.CTkLabel(info_box, text=f"Customer: {self.order.customer_name}", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"]).grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6))

        # Items list
        items_frame = ctk.CTkScrollableFrame(container, height=130, fg_color="transparent")
        items_frame.pack(fill="x", padx=15, pady=(0, 10))

        for it in self.order.items:
            it_row = ctk.CTkFrame(items_frame, fg_color="transparent")
            it_row.pack(fill="x", pady=2)
            ctk.CTkLabel(it_row, text=f"{it.item_name} x{it.quantity}", font=ctk.CTkFont(size=12), text_color=palette["text_primary"]).pack(side="left")
            ctk.CTkLabel(it_row, text=f"{CURRENCY_SYMBOL}{it.line_total}", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_primary"]).pack(side="right")

        # Calculation Inputs
        calc_box = ctk.CTkFrame(container, fg_color="transparent")
        calc_box.pack(fill="x", padx=15, pady=(0, 10))

        # Discount % input
        disc_row = ctk.CTkFrame(calc_box, fg_color="transparent")
        disc_row.pack(fill="x", pady=3)
        ctk.CTkLabel(disc_row, text="Discount Percentage (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(side="left")
        self.entry_discount = ctk.CTkEntry(disc_row, width=80, height=28)
        self.entry_discount.insert(0, "0")
        self.entry_discount.pack(side="right")
        self.entry_discount.bind("<KeyRelease>", lambda e: self._recalculate())

        # Tax Rate input
        tax_row = ctk.CTkFrame(calc_box, fg_color="transparent")
        tax_row.pack(fill="x", pady=3)
        ctk.CTkLabel(tax_row, text=f"GST Tax Rate (%):", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(side="left")
        self.entry_tax = ctk.CTkEntry(tax_row, width=80, height=28)
        self.entry_tax.insert(0, str(DEFAULT_TAX_RATE))
        self.entry_tax.pack(side="right")
        self.entry_tax.bind("<KeyRelease>", lambda e: self._recalculate())

        # Payment Method Radio
        pay_box = ctk.CTkFrame(container, fg_color="transparent")
        pay_box.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(pay_box, text="Payment Method:", font=ctk.CTkFont(size=12, weight="bold"), text_color=palette["text_secondary"]).pack(anchor="w", pady=(0, 4))
        self.pay_method_var = ctk.StringVar(value="CASH")
        radio_row = ctk.CTkFrame(pay_box, fg_color="transparent")
        radio_row.pack(fill="x")
        for pm in SUPPORTED_PAYMENT_METHODS:
            ctk.CTkRadioButton(radio_row, text=pm, variable=self.pay_method_var, value=pm).pack(side="left", padx=10)

        # Net Summary Display
        sum_box = ctk.CTkFrame(container, fg_color=palette["bg_secondary"], corner_radius=8)
        sum_box.pack(fill="x", padx=15, pady=(0, 15))

        self.lbl_subtotal = ctk.CTkLabel(sum_box, text="Subtotal: ₹0.00", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"])
        self.lbl_subtotal.pack(anchor="w", padx=15, pady=(8, 2))

        self.lbl_tax_amt = ctk.CTkLabel(sum_box, text="Tax (5%): ₹0.00", font=ctk.CTkFont(size=12), text_color=palette["text_secondary"])
        self.lbl_tax_amt.pack(anchor="w", padx=15, pady=2)

        self.lbl_final_total = ctk.CTkLabel(sum_box, text="Net Total: ₹0.00", font=ctk.CTkFont(size=17, weight="bold"), text_color=palette["success"])
        self.lbl_final_total.pack(anchor="w", padx=15, pady=(4, 8))

        self.lbl_error = ctk.CTkLabel(container, text="", font=ctk.CTkFont(size=11), text_color=palette["danger"])
        self.lbl_error.pack(fill="x", padx=15, pady=(0, 5))

        # Bottom Buttons
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=25, pady=(0, 20))

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            width=90,
            height=36,
            fg_color=palette["bg_card"],
            text_color=palette["text_primary"],
            hover_color=palette["bg_secondary"],
            command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_bar,
            text="Finalize & Issue Receipt 🧾",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=palette["accent"],
            hover_color=palette["accent_hover"],
            command=self._handle_finalize
        ).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())

    def _recalculate(self):
        subtotal = sum((it.line_total for it in self.order.items), Decimal("0.00"))
        disc_str = self.entry_discount.get().strip() or "0"
        tax_str = self.entry_tax.get().strip() or "5.0"

        try:
            disc_dec = Decimal(disc_str)
            tax_dec = Decimal(tax_str)
            breakdown = self.billing_svc.calculate_bill_breakdown(subtotal, disc_dec, tax_dec)
            self.lbl_subtotal.configure(text=f"Subtotal: {CURRENCY_SYMBOL}{breakdown['subtotal']}  |  Discount: -{CURRENCY_SYMBOL}{breakdown['discount_amount']}")
            self.lbl_tax_amt.configure(text=f"Tax ({breakdown['tax_rate']}%): +{CURRENCY_SYMBOL}{breakdown['tax_amount']}")
            self.lbl_final_total.configure(text=f"Net Total: {CURRENCY_SYMBOL}{breakdown['final_total']}")
            self.lbl_error.configure(text="")
        except Exception as e:
            self.lbl_error.configure(text="Invalid numeric values for discount or tax.")

    def _handle_finalize(self):
        disc_str = self.entry_discount.get().strip()
        tax_str = self.entry_tax.get().strip()
        pm = self.pay_method_var.get()

        ok, msg, bill = self.billing_svc.finalize_bill(
            order_id=self.order.id,
            payment_method=pm,
            discount_percent_input=disc_str,
            tax_rate_input=tax_str
        )
        if not ok:
            self.lbl_error.configure(text=msg)
            return

        # Generate and show receipt
        receipt_text = self.billing_svc.format_receipt_text(bill, self.order)
        self.destroy()
        ReceiptDialog(self.master, receipt_text)
        self.on_bill_completed(self.order.id)
