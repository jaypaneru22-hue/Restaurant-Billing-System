"""Billing service providing financial calculations, transaction persistence, and receipt formatting."""
from typing import Optional, Tuple, Dict, Any
from decimal import Decimal
from models.bill import Bill
from models.order import Order
from repositories.billing_repository import BillingRepository
from repositories.order_repository import OrderRepository
from config.settings import DEFAULT_TAX_RATE, CURRENCY_SYMBOL
from utils.validators import validate_discount, validate_tax_rate, validate_payment_method
from utils.logger import logger


class BillingService:
    def __init__(self, billing_repo: Optional[BillingRepository] = None, order_repo: Optional[OrderRepository] = None):
        self.billing_repo = billing_repo or BillingRepository()
        self.order_repo = order_repo or OrderRepository()

    def calculate_bill_breakdown(
        self,
        subtotal: Decimal,
        discount_percent: Decimal = Decimal("0.00"),
        tax_rate: Decimal = DEFAULT_TAX_RATE
    ) -> Dict[str, Decimal]:
        """Calculates precise discount, tax, and final total using fixed-point Decimal arithmetic."""
        subtotal = subtotal.quantize(Decimal("0.01"))
        discount_rate = discount_percent.quantize(Decimal("0.01"))
        tax = tax_rate.quantize(Decimal("0.01"))

        # 1. Calculate discount amount
        discount_amount = (subtotal * (discount_rate / Decimal("100.00"))).quantize(Decimal("0.01"))
        discounted_subtotal = (subtotal - discount_amount).quantize(Decimal("0.01"))

        # 2. Calculate tax on discounted subtotal
        tax_amount = (discounted_subtotal * (tax / Decimal("100.00"))).quantize(Decimal("0.01"))

        # 3. Calculate final total
        final_total = (discounted_subtotal + tax_amount).quantize(Decimal("0.01"))

        return {
            "subtotal": subtotal,
            "discount_percent": discount_rate,
            "discount_amount": discount_amount,
            "discounted_subtotal": discounted_subtotal,
            "tax_rate": tax,
            "tax_amount": tax_amount,
            "final_total": final_total
        }

    def finalize_bill(
        self,
        order_id: int,
        payment_method: str,
        discount_percent_input: str | float | Decimal | int = Decimal("0.00"),
        tax_rate_input: str | float | Decimal | int = DEFAULT_TAX_RATE
    ) -> Tuple[bool, str, Optional[Bill]]:
        """Processes and persistently commits a bill, locking the order."""
        # 1. Fetch order
        order = self.order_repo.get_by_id(order_id)
        if not order:
            return False, "Order not found.", None
        if not order.is_pending():
            return False, f"Order is already in '{order.status}' status and cannot be billed.", None
        if not order.items:
            return False, "Cannot bill an order with no items.", None

        # 2. Validate validations
        valid_pay, pay_msg = validate_payment_method(payment_method)
        if not valid_pay:
            return False, pay_msg, None

        valid_disc, disc_msg, discount_percent = validate_discount(discount_percent_input, Decimal("50.0"))
        if not valid_disc:
            return False, disc_msg, None

        valid_tax, tax_msg, tax_rate = validate_tax_rate(tax_rate_input)
        if not valid_tax:
            return False, tax_msg, None

        # 3. Check if bill already exists
        existing_bill = self.billing_repo.get_by_order_id(order_id)
        if existing_bill:
            return False, f"Bill already exists for this order: {existing_bill.bill_number}", existing_bill

        # 4. Compute subtotal from line items
        subtotal = sum((item.line_total for item in order.items), Decimal("0.00")).quantize(Decimal("0.01"))

        breakdown = self.calculate_bill_breakdown(
            subtotal=subtotal,
            discount_percent=discount_percent,
            tax_rate=tax_rate
        )

        try:
            bill = self.billing_repo.create_bill(
                order_id=order_id,
                subtotal=breakdown["subtotal"],
                tax_rate=breakdown["tax_rate"],
                tax_amount=breakdown["tax_amount"],
                discount_percent=breakdown["discount_percent"],
                discount_amount=breakdown["discount_amount"],
                final_total=breakdown["final_total"],
                payment_method=payment_method
            )
            return True, "Bill finalized and payment recorded successfully.", bill
        except Exception as e:
            logger.error(f"Error finalizing bill for order id={order_id}: {e}", exc_info=True)
            return False, f"Database error finalizing bill: {e}", None

    def get_bill_for_order(self, order_id: int) -> Optional[Bill]:
        return self.billing_repo.get_by_order_id(order_id)

    def get_bill_by_number(self, bill_number: str) -> Optional[Bill]:
        return self.billing_repo.get_by_bill_number(bill_number)

    def format_receipt_text(self, bill: Bill, order: Order, restaurant_name: str = "TQM GOURMET RESTAURANT") -> str:
        """Generates an itemized receipt text representation suitable for thermal printing or display."""
        width = 46
        lines = []
        lines.append("=" * width)
        lines.append(restaurant_name.center(width))
        lines.append("BBAT104 Total Quality Management Project".center(width))
        lines.append("Registration No: 2410302024".center(width))
        lines.append("=" * width)
        lines.append(f"Bill No:   {bill.bill_number}")
        lines.append(f"Order No:  {order.order_number}")
        lines.append(f"Date/Time: {bill.billed_at or order.created_at or 'N/A'}")
        lines.append(f"Table:     {order.table_number:<15} Customer: {order.customer_name}")
        lines.append("-" * width)
        lines.append(f"{'Item':<22}{'Qty':>4} {'Price':>8} {'Total':>10}")
        lines.append("-" * width)

        for item in order.items:
            name = item.item_name[:20]
            lines.append(
                f"{name:<22}{item.quantity:>4} {str(item.unit_price):>8} {str(item.line_total):>10}"
            )

        lines.append("-" * width)
        lines.append(f"{'Subtotal:':<34} {CURRENCY_SYMBOL}{str(bill.subtotal):>10}")

        if bill.discount_percent > Decimal("0.00"):
            lines.append(f"{f'Discount ({bill.discount_percent}%):':<34}-{CURRENCY_SYMBOL}{str(bill.discount_amount):>10}")

        lines.append(f"{f'GST ({bill.tax_rate}%):':<34} {CURRENCY_SYMBOL}{str(bill.tax_amount):>10}")
        lines.append("=" * width)
        lines.append(f"{'NET PAYABLE AMOUNT:':<34} {CURRENCY_SYMBOL}{str(bill.final_total):>10}")
        lines.append("=" * width)
        lines.append(f"Payment Method: {bill.payment_method}  |  Status: {bill.payment_status}")
        lines.append("-" * width)
        lines.append("Thank you for dining with us!".center(width))
        lines.append("Quality Goal: Q08 - Improve User Satisfaction".center(width))
        lines.append("=" * width)

        return "\n".join(lines)


# Global billing service instance
billing_service = BillingService()
