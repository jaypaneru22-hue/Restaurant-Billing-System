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

# Brand Asset Paths
LOGO_IMAGE_PATH = ASSETS_DIR / "restopro_logo.png"
LOGO_JPG_PATH = ASSETS_DIR / "restopro_logo.jpg"
APP_ICON_PNG = ASSETS_DIR / "restopro_icon.png"
APP_ICON_ICO = ASSETS_DIR / "restopro_icon.ico"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Database Paths
DEFAULT_DB_PATH = DATA_DIR / "restaurant.db"
TEST_DB_PATH = BASE_DIR / "tests" / "test_restaurant.db"

# Financial & Tax Settings
CURRENCY_SYMBOL = "₹"
DEFAULT_TAX_RATE = Decimal("5.0")  # 5.0% Restaurant Goods and Services Tax (GST)
MAX_DISCOUNT_PERCENT = Decimal("50.0")

# UI Theme Configuration
SUPPORTED_THEMES = ["light", "dark"]
DEFAULT_THEME = "light"

# Color Palettes for High-Contrast Modern Ergonomics (Concept B: Midnight Obsidian - Dribbble SaaS Reference)
THEME_PALETTES = {
    "dark": {
        # Midnight Obsidian Dark Mode (Exact Design System)
        "app_bg": "#0B0B12",
        "bg_primary": "#111118",
        "bg_secondary": "#171720",
        "bg_card": "#171720",
        "bg_card_elevated": "#1D1D29",
        "bg_card_subtle": "#171720",

        # Sidebar (Deep Obsidian Charcoal)
        "sidebar_bg": "#101019",
        "sidebar_secondary": "#171720",
        "sidebar_hover": "#1D1D29",
        "sidebar_active": "#6657F5",
        "sidebar_text": "#F5F5F7",
        "sidebar_text_muted": "#A1A1B5",
        "sidebar_border": "#292938",

        # Header Bar
        "header_bg": "#111118",
        "header_text": "#F5F5F7",
        "header_border": "#292938",

        # Typography (Crisp White & Muted Slate - High Contrast)
        "heading": "#FFFFFF",
        "section_heading": "#F5F5F7",
        "form_label": "#F5F5F7",
        "body": "#F5F5F7",
        "text_primary": "#F5F5F7",
        "text_secondary": "#A1A1B5",
        "text_muted": "#71718A",

        # Accents & Interactive (Electric Violet & Purple Accents)
        "accent": "#6657F5",
        "accent_hover": "#5546E8",
        "accent_light": "#1D1D29",
        "accent_secondary": "#8B5CF6",
        "electric_blue": "#38BDF8",

        # Status & Quality Feedback
        "success": "#22C55E",
        "success_light": "#052E16",
        "warning": "#F59E0B",
        "warning_light": "#451A03",
        "danger": "#EF4444",
        "danger_light": "#450A0A",
        "border": "#292938",
    },
    "light": {
        # Light Mode Counterpart (Deep Navy Sidebar + Pure White Workspace)
        "app_bg": "#F8FAFC",
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F8FAFC",
        "bg_card": "#FFFFFF",
        "bg_card_elevated": "#FFFFFF",
        "bg_card_subtle": "#F1F5F9",

        # Sidebar (Deep Navy)
        "sidebar_bg": "#173B70",
        "sidebar_secondary": "#245A9B",
        "sidebar_hover": "#245A9B",
        "sidebar_active": "#2563EB",
        "sidebar_text": "#FFFFFF",
        "sidebar_text_muted": "#BFDBFE",
        "sidebar_border": "#1E3A8A",

        # Header Bar
        "header_bg": "#FFFFFF",
        "header_text": "#173B70",
        "header_border": "#E2E8F0",

        # Typography (High Contrast Navy & Slate)
        "heading": "#173B70",
        "section_heading": "#1E293B",
        "form_label": "#334155",
        "body": "#334155",
        "text_primary": "#1E293B",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",

        # Accents & Interactive
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "accent_light": "#EFF6FF",
        "accent_secondary": "#7C3AED",
        "electric_blue": "#0284C7",

        # Status & Quality Feedback
        "success": "#16A34A",
        "success_light": "#DCFCE7",
        "warning": "#F59E0B",
        "warning_light": "#FEF3C7",
        "danger": "#DC2626",
        "danger_light": "#FEE2E2",
        "border": "#E2E8F0",
    }
}

# User Roles
ROLE_ADMIN = "ADMIN"
ROLE_MANAGER = "MANAGER"
ROLE_CASHIER = "CASHIER"
ROLE_CHEF = "CHEF"
ROLE_WAITER = "WAITER"
ROLE_CUSTOMER = "CUSTOMER"
VALID_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER, ROLE_CHEF, ROLE_WAITER, ROLE_CUSTOMER]

# Order Status Constants
ORDER_STATUS_PENDING = "PENDING"
ORDER_STATUS_ACCEPTED = "ACCEPTED"
ORDER_STATUS_PREPARING = "PREPARING"
ORDER_STATUS_READY = "READY"
ORDER_STATUS_PICKED_UP = "PICKED_UP"
ORDER_STATUS_SERVED = "SERVED"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_CANCELLED = "CANCELLED"
VALID_ORDER_STATUSES = [
    ORDER_STATUS_PENDING,
    ORDER_STATUS_ACCEPTED,
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_READY,
    ORDER_STATUS_PICKED_UP,
    ORDER_STATUS_SERVED,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_CANCELLED
]

# Payment Methods
PAYMENT_CASH = "CASH"
PAYMENT_CARD = "CARD"
PAYMENT_UPI = "UPI"
PAYMENT_SPLIT = "SPLIT"
SUPPORTED_PAYMENT_METHODS = [PAYMENT_CASH, PAYMENT_CARD, PAYMENT_UPI, PAYMENT_SPLIT]

# Menu Categories
DEFAULT_CATEGORIES = [
    "Beverages",
    "Starters",
    "Main Course",
    "Breads & Rice",
    "Desserts"
]
