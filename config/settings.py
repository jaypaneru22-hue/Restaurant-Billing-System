"""Application configuration and constants."""
from pathlib import Path
from decimal import Decimal

# Project & Academic Metadata
APP_NAME = "Restaurant Billing System"
APP_VERSION = "1.0.0"
ACADEMIC_SUBJECT = "BBAT104 — Fundamentals of Total Quality Management"
STUDENT_NAME = "Jay Paneru"
REGISTRATION_NUMBER = "2410302024"
QUALITY_GOAL = "Q08 — Improve User Satisfaction"
ACADEMIC_SESSION = "2026–27"

# File System Directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DOCS_DIR = BASE_DIR / "docs"
QUALITY_DIR = BASE_DIR / "quality"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Database Paths
DEFAULT_DB_PATH = DATA_DIR / "restaurant.db"
TEST_DB_PATH = BASE_DIR / "tests" / "test_restaurant.db"

# Financial & Tax Settings
CURRENCY_SYMBOL = "₹"
DEFAULT_TAX_RATE = Decimal("5.0")  # 5.0% Restaurant Goods and Services Tax (GST)
MAX_DISCOUNT_PERCENT = Decimal("50.0")

# UI Theme Configuration
SUPPORTED_THEMES = ["dark", "light"]
DEFAULT_THEME = "dark"

# Color Palettes for High-Contrast Modern Ergonomics
THEME_PALETTES = {
    "dark": {
        "bg_primary": "#1a1a24",
        "bg_secondary": "#242436",
        "bg_card": "#2d2d44",
        "text_primary": "#f8f9fa",
        "text_secondary": "#a0a5b5",
        "accent": "#4f46e5",       # Indigo
        "accent_hover": "#4338ca",
        "success": "#10b981",      # Emerald
        "warning": "#f59e0b",      # Amber
        "danger": "#ef4444",       # Crimson
        "border": "#3d3d5c"
    },
    "light": {
        "bg_primary": "#f3f4f6",
        "bg_secondary": "#ffffff",
        "bg_card": "#ffffff",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
        "accent": "#4f46e5",
        "accent_hover": "#4338ca",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "border": "#e5e7eb"
    }
}

# Order Status Constants
ORDER_STATUS_PENDING = "PENDING"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_CANCELLED = "CANCELLED"
VALID_ORDER_STATUSES = [ORDER_STATUS_PENDING, ORDER_STATUS_COMPLETED, ORDER_STATUS_CANCELLED]

# Payment Methods
PAYMENT_CASH = "CASH"
PAYMENT_CARD = "CARD"
PAYMENT_UPI = "UPI"
SUPPORTED_PAYMENT_METHODS = [PAYMENT_CASH, PAYMENT_CARD, PAYMENT_UPI]

# Menu Categories
DEFAULT_CATEGORIES = [
    "Beverages",
    "Starters",
    "Main Course",
    "Breads & Rice",
    "Desserts"
]
