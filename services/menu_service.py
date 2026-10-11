"""Menu management business logic service with validation and Poka-Yoke checks."""
from typing import Optional, List, Tuple
from decimal import Decimal
from models.menu_item import MenuItem
from repositories.menu_repository import MenuRepository
from utils.validators import validate_menu_item
from utils.logger import logger


class MenuService:
    def __init__(self, menu_repo: Optional[MenuRepository] = None):
        self.menu_repo = menu_repo or MenuRepository()

    def add_item(self, name: str, category: str, price_input: str | float | Decimal | int, is_available: bool = True) -> Tuple[bool, str, Optional[MenuItem]]:
        valid, msg, dec_price = validate_menu_item(name, category, price_input)
        if not valid:
            return False, msg, None

        # Check for duplicates in category
        existing = self.menu_repo.get_by_name_and_category(name, category)
        if existing:
            return False, f"An item named '{name}' already exists in category '{category}'.", None

        try:
            item = self.menu_repo.create(name, category, dec_price, is_available)
            return True, "Menu item added successfully.", item
        except Exception as e:
            logger.error(f"Error creating menu item: {e}", exc_info=True)
            return False, f"Database error creating menu item: {e}", None

    def update_item(self, item_id: int, name: str, category: str, price_input: str | float | Decimal | int, is_available: bool) -> Tuple[bool, str]:
        valid, msg, dec_price = validate_menu_item(name, category, price_input)
        if not valid:
            return False, msg

        existing = self.menu_repo.get_by_id(item_id)
        if not existing:
            return False, "Menu item not found."

        duplicate = self.menu_repo.get_by_name_and_category(name, category)
        if duplicate and duplicate.id != item_id:
            return False, f"Another item named '{name}' already exists in category '{category}'."

        try:
            success = self.menu_repo.update(item_id, name, category, dec_price, is_available)
            if success:
                return True, "Menu item updated successfully."
            return False, "Update failed."
        except Exception as e:
            logger.error(f"Error updating menu item id={item_id}: {e}", exc_info=True)
            return False, f"Database error updating menu item: {e}"

    def delete_item(self, item_id: int) -> Tuple[bool, str]:
        existing = self.menu_repo.get_by_id(item_id)
        if not existing:
            return False, "Menu item not found."

        try:
            success = self.menu_repo.delete(item_id)
            if success:
                return True, "Menu item removed/archived successfully."
            return False, "Failed to delete menu item."
        except Exception as e:
            logger.error(f"Error deleting menu item id={item_id}: {e}", exc_info=True)
            return False, f"Database error deleting menu item: {e}"

    def get_all_items(self, available_only: bool = False) -> List[MenuItem]:
        return self.menu_repo.list_all(available_only=available_only)

    def search_items(self, query: str = "", category: Optional[str] = None, available_only: bool = False) -> List[MenuItem]:
        return self.menu_repo.search(query=query, category=category, available_only=available_only)

    def get_categories(self) -> List[str]:
        return self.menu_repo.get_categories()


# Global menu service instance
menu_service = MenuService()
