"""Brand assets manager providing optimized logo and icon loading for RestoPro.

Maintains strict aspect ratio, applies Lanczos high-sharpness resampling,
and manages memory caching for both Midnight Obsidian Dark Mode and Light Mode.
"""
from pathlib import Path
from typing import Optional, Tuple
import sys
from PIL import Image, ImageDraw
import customtkinter as ctk

from config.settings import ASSETS_DIR
from utils.logger import logger

# Canonical paths
LOGO_PATH = ASSETS_DIR / "restopro_logo.png"
LOGO_JPG_PATH = ASSETS_DIR / "restopro_logo.jpg"
ICON_PATH = ASSETS_DIR / "restopro_icon.png"
ICON_ICO_PATH = ASSETS_DIR / "restopro_icon.ico"
LOGO_TRANSPARENT_PATH = ASSETS_DIR / "restopro_logo_transparent.png"
AMBIENCE_PATH = ASSETS_DIR / "restaurant_ambience.jpg"

# Original dimensions of supplied asset
ORIGINAL_LOGO_WIDTH = 1024
ORIGINAL_LOGO_HEIGHT = 682
LOGO_ASPECT_RATIO = ORIGINAL_LOGO_WIDTH / ORIGINAL_LOGO_HEIGHT  # ~1.501466

# Memory cache for CTkImage objects: key is (asset_type, width, height)
_IMAGE_CACHE = {}
_PIL_CACHE = {}


def get_logo_dimensions(target_width: Optional[int] = None, target_height: Optional[int] = None) -> Tuple[int, int]:
    """Calculates dimensions maintaining exact original aspect ratio without distortion."""
    if target_width is not None and target_height is not None:
        # Check aspect ratio discrepancy
        current_ratio = target_width / target_height
        if abs(current_ratio - LOGO_ASPECT_RATIO) > 0.05:
            # Recalculate height to strictly preserve aspect ratio
            corrected_height = round(target_width / LOGO_ASPECT_RATIO)
            logger.debug(f"Adjusted logo height from {target_height} to {corrected_height} to preserve aspect ratio")
            return target_width, corrected_height
        return target_width, target_height
    elif target_width is not None:
        return target_width, round(target_width / LOGO_ASPECT_RATIO)
    elif target_height is not None:
        return round(target_height * LOGO_ASPECT_RATIO), target_height
    else:
        # Default prominent width
        default_w = 210
        return default_w, round(default_w / LOGO_ASPECT_RATIO)


def get_brand_logo(
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    use_transparent_in_light: bool = False
) -> Optional[ctk.CTkImage]:
    """Returns a high-sharpness CTkImage for the RestoPro logo.

    Strictly preserves aspect ratio and uses Lanczos resampling.
    Caches in memory for instant subsequent theme toggles and view transitions.
    """
    w, h = get_logo_dimensions(target_width, target_height)
    cache_key = ("logo", w, h, use_transparent_in_light)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    logo_file = LOGO_PATH if LOGO_PATH.exists() else LOGO_JPG_PATH
    if not logo_file.exists():
        logger.warning(f"RestoPro logo file not found at {logo_file}")
        return None

    try:
        # Load dark image (exact supplied asset)
        pil_dark = _get_resampled_pil(logo_file, w, h)

        # Load light image
        if use_transparent_in_light and LOGO_TRANSPARENT_PATH.exists():
            pil_light = _get_resampled_pil(LOGO_TRANSPARENT_PATH, w, h)
        else:
            pil_light = pil_dark

        ctk_img = ctk.CTkImage(
            light_image=pil_light,
            dark_image=pil_dark,
            size=(w, h)
        )
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        logger.error(f"Failed to load brand logo: {e}")
        return None


def get_brand_icon(size: int = 40) -> Optional[ctk.CTkImage]:
    """Returns a high-sharpness CTkImage for the square RestoPro emblem icon."""
    cache_key = ("icon", size, size)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    if not ICON_PATH.exists():
        logger.warning(f"RestoPro icon file not found at {ICON_PATH}")
        return None

    try:
        pil_icon = _get_resampled_pil(ICON_PATH, size, size)
        ctk_img = ctk.CTkImage(
            light_image=pil_icon,
            dark_image=pil_icon,
            size=(size, size)
        )
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        logger.error(f"Failed to load brand icon: {e}")
        return None


def _get_resampled_pil(file_path: Path, width: int, height: int) -> Image.Image:
    """Loads and resamples a PIL image using Lanczos interpolation, with caching."""
    cache_key = (str(file_path), width, height)
    if cache_key in _PIL_CACHE:
        return _PIL_CACHE[cache_key]

    with Image.open(file_path) as raw:
        # Convert to RGBA for clean alpha handling if PNG, otherwise RGB
        mode = "RGBA" if raw.mode in ("RGBA", "LA") or raw.format == "PNG" else "RGB"
        img = raw.convert(mode)
        resampled = img.resize((width, height), Image.Resampling.LANCZOS)
        _PIL_CACHE[cache_key] = resampled
        return resampled


def get_ambience_banner(
    width: int,
    height: int,
    is_dark: bool = True,
) -> Optional[ctk.CTkImage]:
    """Returns a cinematic restaurant ambience banner with a dark overlay gradient.

    Crops to fill the target dimensions (center-crop), then composites a
    dark obsidian gradient overlay so text placed on top remains readable.
    Caches results in memory for instant theme toggles.
    """
    cache_key = ("ambience", width, height, is_dark)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    src = AMBIENCE_PATH
    if not src.exists():
        logger.warning(f"Restaurant ambience image not found at {src}")
        return None

    try:
        raw = Image.open(src).convert("RGB")
        orig_w, orig_h = raw.size
        aspect_target = width / height
        aspect_orig = orig_w / orig_h

        # Center-crop to target aspect ratio, then resize
        if aspect_orig > aspect_target:
            new_w = int(orig_h * aspect_target)
            left = (orig_w - new_w) // 2
            cropped = raw.crop((left, 0, left + new_w, orig_h))
        else:
            new_h = int(orig_w / aspect_target)
            top = (orig_h - new_h) // 2
            cropped = raw.crop((0, top, orig_w, top + new_h))

        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)

        # Overlay dark obsidian gradient (top→bottom increasing opacity)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for y in range(height):
            ratio = y / height
            if is_dark:
                alpha = int(165 + (230 - 165) * ratio)
                color = (11, 11, 20, alpha)
            else:
                alpha = int(140 + (210 - 140) * ratio)
                color = (20, 25, 50, alpha)
            draw.line([(0, y), (width, y)], fill=color)

        base_rgba = resized.convert("RGBA")
        composited = Image.alpha_composite(base_rgba, overlay).convert("RGB")

        ctk_img = ctk.CTkImage(
            light_image=composited,
            dark_image=composited,
            size=(width, height),
        )
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        logger.error(f"Failed to create ambience banner: {e}")
        return None


def apply_window_icon(window: ctk.CTk | ctk.CTkToplevel) -> bool:
    """Applies the RestoPro icon to the window titlebar and taskbar."""
    if not ICON_ICO_PATH.exists() and not ICON_PATH.exists():
        return False

    try:
        if sys.platform == "win32" and ICON_ICO_PATH.exists():
            window.iconbitmap(str(ICON_ICO_PATH))
            return True
        elif ICON_PATH.exists():
            from PIL import ImageTk
            icon_img = _get_resampled_pil(ICON_PATH, 64, 64)
            photo = ImageTk.PhotoImage(icon_img)
            window.iconphoto(True, photo)
            # Retain reference to prevent garbage collection
            setattr(window, "_icon_photo_ref", photo)
            return True
    except Exception as e:
        logger.debug(f"Notice: OS window icon assignment skipped ({e})")
    return False
