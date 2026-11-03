"""Automated unit tests for RestoPro brand assets, aspect ratio preservation, and image caching."""
import pytest
from pathlib import Path
from PIL import Image
import customtkinter as ctk

from config.settings import ASSETS_DIR, LOGO_IMAGE_PATH, APP_ICON_PNG, APP_ICON_ICO
from utils.brand_assets import (
    get_brand_logo,
    get_brand_icon,
    get_logo_dimensions,
    apply_window_icon,
    LOGO_ASPECT_RATIO,
    ORIGINAL_LOGO_WIDTH,
    ORIGINAL_LOGO_HEIGHT
)


def test_logo_asset_exists_and_dimensions():
    """Verifies that the canonical RestoPro logo exists and matches supplied dimensions."""
    assert LOGO_IMAGE_PATH.exists(), f"Logo missing at {LOGO_IMAGE_PATH}"
    with Image.open(LOGO_IMAGE_PATH) as img:
        assert img.size == (ORIGINAL_LOGO_WIDTH, ORIGINAL_LOGO_HEIGHT)
        assert img.size == (1024, 682)


def test_logo_aspect_ratio_preservation():
    """Ensures that logo dimensions strictly preserve the 1024:682 aspect ratio without distortion."""
    # When target width is requested
    w, h = get_logo_dimensions(target_width=210)
    assert w == 210
    assert h == 140
    ratio = w / h
    assert abs(ratio - LOGO_ASPECT_RATIO) < 0.01

    # When target height is requested
    w2, h2 = get_logo_dimensions(target_height=120)
    assert h2 == 120
    assert abs((w2 / h2) - LOGO_ASPECT_RATIO) < 0.01

    # When distorted dimensions are requested, function corrects height to preserve aspect ratio
    w3, h3 = get_logo_dimensions(target_width=210, target_height=300)
    assert w3 == 210
    assert h3 == 140  # Corrected to preserve aspect ratio


def test_brand_icon_is_square():
    """Verifies that the RestoPro emblem icon is a perfect 1:1 square."""
    assert APP_ICON_PNG.exists(), f"Icon missing at {APP_ICON_PNG}"
    with Image.open(APP_ICON_PNG) as icon:
        w, h = icon.size
        assert w == h, f"Icon must be square, got {w}x{h}"
        assert w >= 128


def test_brand_icon_ico_exists():
    """Verifies that multi-resolution Windows .ico file is present."""
    assert APP_ICON_ICO.exists(), f"ICO file missing at {APP_ICON_ICO}"
    assert APP_ICON_ICO.stat().st_size > 1000


def test_get_brand_logo_returns_ctk_image():
    """Verifies CTkImage creation and caching for the RestoPro logo."""
    logo = get_brand_logo(target_width=210)
    assert logo is not None
    assert isinstance(logo, ctk.CTkImage)
    assert logo._size == (210, 140)

    # Calling again should retrieve from memory cache
    logo_cached = get_brand_logo(target_width=210)
    assert logo_cached is logo


def test_get_brand_icon_returns_ctk_image():
    """Verifies CTkImage creation and caching for the RestoPro emblem icon."""
    icon = get_brand_icon(size=36)
    assert icon is not None
    assert isinstance(icon, ctk.CTkImage)
    assert icon._size == (36, 36)

    # Calling again should retrieve from memory cache
    icon_cached = get_brand_icon(size=36)
    assert icon_cached is icon


def test_apply_window_icon_graceful_execution():
    """Ensures window icon application executes safely with mock or real window."""
    from unittest.mock import MagicMock
    mock_win = MagicMock()
    result = apply_window_icon(mock_win)
    assert isinstance(result, bool)
    assert result is True
    mock_win.iconbitmap.assert_called_once()
