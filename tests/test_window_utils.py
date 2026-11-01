"""Unit tests for window_utils geometry and centering functions."""
from unittest.mock import MagicMock
from utils.window_utils import center_window, center_dialog


def test_center_window_calculation():
    """Verify center_window clamps within screen bounds and computes correct offsets."""
    mock_win = MagicMock()
    mock_win.winfo_screenwidth.return_value = 1920
    mock_win.winfo_screenheight.return_value = 1080

    center_window(mock_win, target_width=1240, target_height=750, min_width=1024, min_height=640)

    # Expected: width=1240, height=750, x=(1920-1240)//2 = 340, y=(1080-750)//2 = 165
    mock_win.geometry.assert_called_once_with("1240x750+340+165")
    mock_win.minsize.assert_called_once_with(1024, 640)
    mock_win.resizable.assert_called_once_with(True, True)


def test_center_window_small_screen_clamping():
    """Verify center_window adapts to smaller screens like 1366x768 laptops."""
    mock_win = MagicMock()
    mock_win.winfo_screenwidth.return_value = 1366
    mock_win.winfo_screenheight.return_value = 768

    center_window(mock_win, target_width=1400, target_height=900, min_width=1024, min_height=640)

    # avail_w = 1366 - 40 = 1326; avail_h = 768 - 70 = 698
    # target was 1400x900 -> clamped to 1326x698
    # x = (1366 - 1326)//2 = 20, y = (768 - 698)//2 = 35
    mock_win.geometry.assert_called_once_with("1326x698+20+35")


def test_center_dialog_relative_to_parent():
    """Verify dialog is centered relative to the parent window's coordinates."""
    mock_dialog = MagicMock()
    mock_dialog.winfo_screenwidth.return_value = 1920
    mock_dialog.winfo_screenheight.return_value = 1080

    mock_parent = MagicMock()
    mock_parent.winfo_exists.return_value = True
    mock_parent.winfo_width.return_value = 1200
    mock_parent.winfo_height.return_value = 700
    mock_parent.winfo_rootx.return_value = 300
    mock_parent.winfo_rooty.return_value = 150

    center_dialog(mock_dialog, parent=mock_parent, target_width=500, target_height=400)

    # x = 300 + (1200 - 500)//2 = 300 + 350 = 650
    # y = 150 + (700 - 400)//2 = 150 + 150 = 300
    mock_dialog.geometry.assert_called_once_with("500x400+650+300")


def test_center_dialog_standalone_fallback():
    """Verify dialog centers on monitor when parent is None or destroyed."""
    mock_dialog = MagicMock()
    mock_dialog.winfo_screenwidth.return_value = 1920
    mock_dialog.winfo_screenheight.return_value = 1080

    center_dialog(mock_dialog, parent=None, target_width=500, target_height=400)

    # Fallback: x = (1920 - 500)//2 = 710, y = (1080 - 400)//2 = 340
    mock_dialog.geometry.assert_called_once_with("500x400+710+340")
