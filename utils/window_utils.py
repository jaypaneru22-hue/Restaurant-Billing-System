"""Window geometry and monitor centering utilities for responsive desktop display."""
import tkinter as tk
from typing import Optional


def center_window(
    window,
    target_width: int = 1240,
    target_height: int = 750,
    min_width: int = 1024,
    min_height: int = 640
) -> None:
    """Centers the root application window on the user's primary monitor.

    Calculates dynamic display coordinates using the monitor resolution,
    ensures the window fits comfortably within available bounds, and avoids
    fixed hardcoded offsets.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Clamp to monitor dimensions with padding for taskbar and titlebar
    avail_w = max(min_width, screen_width - 40)
    avail_h = max(min_height, screen_height - 70)

    width = min(target_width, avail_w)
    height = min(target_height, avail_h)

    # Compute centered coordinates
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(min(min_width, width), min(min_height, height))
    window.resizable(True, True)


def center_dialog(
    dialog,
    parent=None,
    target_width: int = 540,
    target_height: int = 620,
    min_width: Optional[int] = None,
    min_height: Optional[int] = None
) -> None:
    """Centers a modal top-level dialog relative to its parent window.

    Falls back to centering on the primary monitor if parent is unavailable.
    """
    dialog.update_idletasks()
    screen_w = dialog.winfo_screenwidth()
    screen_h = dialog.winfo_screenheight()

    target_width = min(target_width, screen_w - 30)
    target_height = min(target_height, screen_h - 60)

    if parent and parent.winfo_exists():
        try:
            parent.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()

            x = px + max(0, (pw - target_width) // 2)
            y = py + max(0, (ph - target_height) // 2)

            # Ensure dialog doesn't spill beyond screen edges
            x = max(10, min(x, screen_w - target_width - 10))
            y = max(10, min(y, screen_h - target_height - 30))
        except Exception:
            x = max(0, (screen_w - target_width) // 2)
            y = max(0, (screen_h - target_height) // 2)
    else:
        x = max(0, (screen_w - target_width) // 2)
        y = max(0, (screen_h - target_height) // 2)

    dialog.geometry(f"{target_width}x{target_height}+{x}+{y}")
    if min_width and min_height:
        dialog.minsize(min(min_width, target_width), min(min_height, target_height))
