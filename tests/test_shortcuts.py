"""Unit tests for keyboard shortcuts, input focus guards, and design system palettes (Q08-F3 & Q08-F4)."""
import pytest
from unittest.mock import MagicMock
from config.settings import THEME_PALETTES, DEFAULT_THEME
from ui.main_window import MainWindow


def test_theme_palette_keys_completeness():
    """Verifies both light (blue-sidebar/white-workspace) and dark palettes define all required semantic tokens."""
    required_keys = [
        "sidebar_bg",
        "sidebar_hover",
        "sidebar_active",
        "sidebar_text",
        "header_bg",
        "header_text",
        "bg_primary",
        "bg_secondary",
        "bg_card",
        "heading",
        "text_primary",
        "text_secondary",
        "accent",
        "accent_hover",
        "success",
        "warning",
        "danger",
        "border",
    ]
    for theme_name in ["light", "dark"]:
        assert theme_name in THEME_PALETTES
        palette = THEME_PALETTES[theme_name]
        for key in required_keys:
            assert key in palette, f"Key '{key}' missing from '{theme_name}' palette"

    # Verify light theme uses user-specified navy sidebar and white workspace
    light = THEME_PALETTES["light"]
    assert light["sidebar_bg"].upper() == "#173B70"
    assert light["bg_primary"].upper() == "#FFFFFF"
    assert light["heading"].upper() == "#173B70"
    assert light["accent"].upper() == "#2563EB"


def test_default_theme_is_light():
    """Verifies default theme is light mode with the professional blue sidebar."""
    assert DEFAULT_THEME == "light"


def test_can_trigger_shortcut_guard():
    """Poka-Yoke verification: Ensures shortcut accelerators are prevented when user is editing text inputs."""
    # Create a mock MainWindow instance without invoking full Tkinter loop
    mw = object.__new__(MainWindow)

    # Case 1: No focused widget -> shortcut should trigger
    mock_toplevel = MagicMock()
    mock_toplevel.focus_get.return_value = None
    mw.winfo_toplevel = MagicMock(return_value=mock_toplevel)
    assert mw._can_trigger_shortcut() is True

    # Case 2: Non-entry widget focused (e.g. Frame, Label, Button) -> shortcut should trigger
    mock_button = MagicMock()
    mock_button.winfo_class.return_value = "Button"
    mock_button.master = None
    mock_toplevel.focus_get.return_value = mock_button
    assert mw._can_trigger_shortcut() is True

    # Case 3: Standard Tkinter Entry focused -> shortcut MUST be blocked
    mock_entry = MagicMock()
    mock_entry.winfo_class.return_value = "Entry"
    mock_entry.master = None
    mock_toplevel.focus_get.return_value = mock_entry
    assert mw._can_trigger_shortcut() is False

    # Case 4: Standard Tkinter Text/Textbox focused -> shortcut MUST be blocked
    mock_text = MagicMock()
    mock_text.winfo_class.return_value = "Text"
    mock_text.master = None
    mock_toplevel.focus_get.return_value = mock_text
    assert mw._can_trigger_shortcut() is False

    # Case 5: CustomTkinter CTkEntry internal canvas/entry focused -> shortcut MUST be blocked
    mock_ctk_inner = MagicMock()
    mock_ctk_inner.winfo_class.return_value = "Entry"
    mock_ctk_parent = MagicMock()
    mock_ctk_parent.winfo_class.return_value = "CTkEntry"
    mock_ctk_inner.master = mock_ctk_parent
    mock_toplevel.focus_get.return_value = mock_ctk_inner
    assert mw._can_trigger_shortcut() is False
