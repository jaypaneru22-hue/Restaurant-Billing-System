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
SUPPORTED_THEMES = ["light", "dark"]
DEFAULT_THEME = "light"

# Color Palettes for High-Contrast Modern Ergonomics (Part B Design Direction: Blue Sidebar + White Workspace)
THEME_PALETTES = {
    "light": {
        # Sidebar (Deep Blue / Navy)
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

        # Workspace & Surfaces (Clean White + Light Grey Sections)
        "bg_primary": "#FFFFFF",
        "bg_secondary": "#F8FAFC",
        "bg_card": "#FFFFFF",
        "bg_card_subtle": "#F1F5F9",

        # Typography (High Contrast Navy & Slate)
        "heading": "#173B70",            # Main page headings: dark navy
        "section_heading": "#1E293B",    # Section headings: dark readable slate
        "form_label": "#334155",         # Form labels: readable dark grey
        "body": "#334155",               # Body text: dark slate
        "text_primary": "#1E293B",       # Main text: dark slate
        "text_secondary": "#64748B",     # Secondary text: muted slate
        "text_muted": "#94A3B8",         # Subtle hints & placeholders

        # Brand Accents & Interactive Elements
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "accent_light": "#EFF6FF",

        # Status & Quality Feedback
        "success": "#16A34A",
        "success_light": "#DCFCE7",
        "warning": "#F59E0B",
        "warning_light": "#FEF3C7",
        "danger": "#DC2626",
        "danger_light": "#FEE2E2",
        "border": "#E2E8F0",
    },
    "dark": {
        # Sidebar (Deep Slate Navy)
        "sidebar_bg": "#0B192C",
        "sidebar_secondary": "#1E3E62",
        "sidebar_hover": "#1E3E62",
        "sidebar_active": "#2563EB",
        "sidebar_text": "#FFFFFF",
        "sidebar_text_muted": "#94A3B8",
        "sidebar_border": "#1E293B",

        # Header Bar
        "header_bg": "#1E293B",
        "header_text": "#F8FAFC",
        "header_border": "#334155",

        # Workspace & Surfaces
        "bg_primary": "#0F172A",
        "bg_secondary": "#1E293B",
        "bg_card": "#1E293B",
        "bg_card_subtle": "#253347",

        # Typography (High Contrast for Dark Mode)
        "heading": "#F8FAFC",            # Main page headings: crisp white/slate
        "section_heading": "#F1F5F9",    # Section headings: light slate
        "form_label": "#E2E8F0",         # Form labels: light grey
        "body": "#E2E8F0",               # Body text: light grey
        "text_primary": "#F8FAFC",       # Main text
        "text_secondary": "#94A3B8",     # Secondary text
        "text_muted": "#64748B",

        # Brand Accents & Interactive Elements
        "accent": "#3B82F6",
        "accent_hover": "#2563EB",
        "accent_light": "#1E3E62",

        # Status & Quality Feedback
        "success": "#10B981",
        "success_light": "#064E3B",
        "warning": "#F59E0B",
        "warning_light": "#78350F",
        "danger": "#EF4444",
        "danger_light": "#7F1D1D",
        "border": "#334155",
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
