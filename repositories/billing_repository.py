"""Repository for bill persistence and invoice history."""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from database.db import DatabaseManager, db
from models.bill import Bill
from utils.logger import logger


class BillingRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def generate_bill_number(self) -> str:
        """Generates a sequential daily bill number: BILL-YYYYMMDD-XXXX."""
        today_str = datetime.now().strftime("%Y%m%d")
        prefix = f"BILL-{today_str}-%"
        row = self.db.fetchone(
            "SELECT COUNT(*) FROM bills WHERE bill_number LIKE ?;",
            (prefix,)
        )
        count = (row[0] if row else 0) + 1
        return f"BILL-{today_str}-{count:04d}"

    def get_by_id(self, bill_id: int) -> Optional[Bill]:
        row = self.db.fetchone(
            """SELECT id, bill_number, order_id, subtotal, tax_rate, tax_amount,
                      discount_percent, discount_amount, final_total, payment_method, payment_status, billed_at
               FROM bills WHERE id = ?;""",
            (bill_id,)
        )
        return self._map_row(row) if row else None

    def get_by_order_id(self, order_id: int) -> Optional[Bill]:
        row = self.db.fetchone(
            """SELECT id, bill_number, order_id, subtotal, tax_rate, tax_amount,
                      discount_percent, discount_amount, final_total, payment_method, payment_status, billed_at
               FROM bills WHERE order_id = ?;""",
            (order_id,)
        )
        return self._map_row(row) if row else None

    def get_by_bill_number(self, bill_number: str) -> Optional[Bill]:
        row = self.db.fetchone(
            """SELECT id, bill_number, order_id, subtotal, tax_rate, tax_amount,
                      discount_percent, discount_amount, final_total, payment_method, payment_status, billed_at
               FROM bills WHERE bill_number = ?;""",
            (bill_number.strip(),)
        )
        return self._map_row(row) if row else None

    def create_bill(
        self,
        order_id: int,
        subtotal: Decimal,
        tax_rate: Decimal,
        tax_amount: Decimal,
        discount_percent: Decimal,
        discount_amount: Decimal,
        final_total: Decimal,
        payment_method: str
    ) -> Bill:
        """Atomically inserts bill and transitions order status to COMPLETED."""
        bill_number = self.generate_bill_number()
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bills (
                    bill_number, order_id, subtotal, tax_rate, tax_amount,
                    discount_percent, discount_amount, final_total, payment_method, payment_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PAID');""",
                (
                    bill_number,
                    order_id,
                    str(subtotal.quantize(Decimal("0.01"))),
                    str(tax_rate.quantize(Decimal("0.01"))),
                    str(tax_amount.quantize(Decimal("0.01"))),
                    str(discount_percent.quantize(Decimal("0.01"))),
                    str(discount_amount.quantize(Decimal("0.01"))),
                    str(final_total.quantize(Decimal("0.01"))),
                    payment_method.upper()
                )
            )
            bill_id = cursor.lastrowid
            cursor.execute(
                "UPDATE orders SET status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (order_id,)
            )
            logger.info(f"Bill created: id={bill_id}, bill_number={bill_number}, total={final_total}")
        return self.get_by_id(bill_id)

    def list_bills(self, limit: int = 50) -> List[Bill]:
        rows = self.db.fetchall(
            """SELECT id, bill_number, order_id, subtotal, tax_rate, tax_amount,
                      discount_percent, discount_amount, final_total, payment_method, payment_status, billed_at
               FROM bills ORDER BY id DESC LIMIT ?;""",
            (limit,)
        )
        return [self._map_row(r) for r in rows]

    def _map_row(self, row) -> Bill:
        return Bill(
            id=row["id"],
            bill_number=row["bill_number"],
            order_id=row["order_id"],
            subtotal=Decimal(str(row["subtotal"])),
            tax_rate=Decimal(str(row["tax_rate"])),
            tax_amount=Decimal(str(row["tax_amount"])),
            discount_percent=Decimal(str(row["discount_percent"])),
            discount_amount=Decimal(str(row["discount_amount"])),
            final_total=Decimal(str(row["final_total"])),
            payment_method=row["payment_method"],
            payment_status=row["payment_status"],
            billed_at=row["billed_at"]
        )
