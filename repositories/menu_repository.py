"""Repository for menu catalog data access."""
from typing import Optional, List
from decimal import Decimal
from database.db import DatabaseManager, db
from models.menu_item import MenuItem
from utils.logger import logger


class MenuRepository:
    def __init__(self, db_manager: DatabaseManager = db):
        self.db = db_manager

    def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        row = self.db.fetchone(
            "SELECT id, name, category, price, is_available, created_at, updated_at FROM menu_items WHERE id = ?;",
            (item_id,)
        )
        return MenuItem.from_row(row) if row else None

    def get_by_name_and_category(self, name: str, category: str) -> Optional[MenuItem]:
        row = self.db.fetchone(
            "SELECT id, name, category, price, is_available, created_at, updated_at FROM menu_items WHERE LOWER(name) = LOWER(?) AND LOWER(category) = LOWER(?);",
            (name.strip(), category.strip())
        )
        return MenuItem.from_row(row) if row else None

    def list_all(self, available_only: bool = False) -> List[MenuItem]:
        sql = "SELECT id, name, category, price, is_available, created_at, updated_at FROM menu_items"
        params = ()
        if available_only:
            sql += " WHERE is_available = 1"
        sql += " ORDER BY category ASC, name ASC;"
        rows = self.db.fetchall(sql, params)
        return [MenuItem.from_row(r) for r in rows]

    def list_by_category(self, category: str, available_only: bool = False) -> List[MenuItem]:
        sql = "SELECT id, name, category, price, is_available, created_at, updated_at FROM menu_items WHERE category = ?"
        params = [category]
        if available_only:
            sql += " AND is_available = 1"
        sql += " ORDER BY name ASC;"
        rows = self.db.fetchall(sql, tuple(params))
        return [MenuItem.from_row(r) for r in rows]

    def search(self, query: str = "", category: Optional[str] = None, available_only: bool = False) -> List[MenuItem]:
        sql = "SELECT id, name, category, price, is_available, created_at, updated_at FROM menu_items WHERE 1=1"
        params = []
        if query and query.strip():
            sql += " AND LOWER(name) LIKE LOWER(?)"
            params.append(f"%{query.strip()}%")
        if category and category.strip() and category != "All":
            sql += " AND category = ?"
            params.append(category.strip())
        if available_only:
            sql += " AND is_available = 1"
        sql += " ORDER BY category ASC, name ASC;"
        rows = self.db.fetchall(sql, tuple(params))
        return [MenuItem.from_row(r) for r in rows]

    def create(self, name: str, category: str, price: Decimal, is_available: bool = True) -> MenuItem:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO menu_items (name, category, price, is_available)
                   VALUES (?, ?, ?, ?);""",
                (name.strip(), category.strip(), str(price.quantize(Decimal("0.01"))), 1 if is_available else 0)
            )
            item_id = cursor.lastrowid
            logger.info(f"Menu item created: id={item_id}, name='{name}', price={price}")
        return self.get_by_id(item_id)

    def update(self, item_id: int, name: str, category: str, price: Decimal, is_available: bool) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE menu_items
                   SET name = ?, category = ?, price = ?, is_available = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?;""",
                (name.strip(), category.strip(), str(price.quantize(Decimal("0.01"))), 1 if is_available else 0, item_id)
            )
            logger.info(f"Menu item updated: id={item_id}, name='{name}'")
            return cursor.rowcount > 0

    def delete(self, item_id: int) -> bool:
        """Deletes a menu item. If referenced by past orders, marks as unavailable for integrity."""
        # Check if item is referenced in order_items
        row = self.db.fetchone("SELECT COUNT(*) FROM order_items WHERE menu_item_id = ?;", (item_id,))
        count = row[0] if row else 0
        with self.db.transaction() as conn:
            cursor = conn.cursor()
            if count > 0:
                # Historical preservation: soft delete / disable
                cursor.execute(
                    "UPDATE menu_items SET is_available = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (item_id,)
                )
                logger.info(f"Menu item id={item_id} referenced in orders; archived by setting is_available=0.")
            else:
                cursor.execute("DELETE FROM menu_items WHERE id = ?;", (item_id,))
                logger.info(f"Menu item id={item_id} permanently removed.")
            return cursor.rowcount > 0

    def get_categories(self) -> List[str]:
        rows = self.db.fetchall("SELECT DISTINCT category FROM menu_items ORDER BY category ASC;")
        return [r["category"] for r in rows]
