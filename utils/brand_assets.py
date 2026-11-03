"""Brand assets manager providing optimized logo and icon loading for RestoPro.

Maintains strict aspect ratio, applies Lanczos high-sharpness resampling,
and manages memory caching for both Midnight Obsidian Dark Mode and Light Mode.
"""
from pathlib import Path
from typing import Optional, Tuple
import sys
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk

from config.settings import ASSETS_DIR
from utils.logger import logger

# Canonical paths
LOGO_PATH = ASSETS_DIR / "restopro_logo.png"
LOGO_JPG_PATH = ASSETS_DIR / "restopro_logo.jpg"
ICON_PATH = ASSETS_DIR / "restopro_icon.png"
ICON_ICO_PATH = ASSETS_DIR / "restopro_icon.ico"
LOGO_TRANSPARENT_PATH = ASSETS_DIR / "restopro_logo_transparent.png"
LOGO_LIGHT_PATH = ASSETS_DIR / "restopro_logo_light.png"
AMBIENCE_PATH = ASSETS_DIR / "restaurant_ambience.jpg"

# Original dimensions of supplied asset
ORIGINAL_LOGO_WIDTH = 1024
ORIGINAL_LOGO_HEIGHT = 682
LOGO_ASPECT_RATIO = ORIGINAL_LOGO_WIDTH / ORIGINAL_LOGO_HEIGHT  # ~1.501466

# Memory cache for CTkImage objects
_IMAGE_CACHE = {}
_PIL_CACHE = {}


def get_logo_dimensions(target_width: Optional[int] = None, target_height: Optional[int] = None) -> Tuple[int, int]:
    """Calculates dimensions maintaining exact original aspect ratio without distortion."""
    if target_width is not None and target_height is not None:
        current_ratio = target_width / target_height
        if abs(current_ratio - LOGO_ASPECT_RATIO) > 0.05:
            corrected_height = round(target_width / LOGO_ASPECT_RATIO)
            return target_width, corrected_height
        return target_width, target_height
    elif target_width is not None:
        return target_width, round(target_width / LOGO_ASPECT_RATIO)
    elif target_height is not None:
        return round(target_height * LOGO_ASPECT_RATIO), target_height
    else:
        default_w = 220
        return default_w, round(default_w / LOGO_ASPECT_RATIO)


def get_brand_logo(
    target_width: Optional[int] = None,
    target_height: Optional[int] = None,
    use_transparent: bool = True
) -> Optional[ctk.CTkImage]:
    """Returns a high-sharpness CTkImage for the RestoPro logo.

    Strictly preserves aspect ratio and uses transparent RGBA assets so no
    rectangular box appears on either dark or light surfaces.
    """
    w, h = get_logo_dimensions(target_width, target_height)
    cache_key = ("logo", w, h, use_transparent)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    dark_source = LOGO_TRANSPARENT_PATH if (use_transparent and LOGO_TRANSPARENT_PATH.exists()) else (LOGO_PATH if LOGO_PATH.exists() else LOGO_JPG_PATH)
    light_source = LOGO_LIGHT_PATH if (use_transparent and LOGO_LIGHT_PATH.exists()) else dark_source

    if not dark_source.exists():
        logger.warning(f"RestoPro logo file not found at {dark_source}")
        return None

    try:
        pil_dark = _get_resampled_pil(dark_source, w, h)
        pil_light = _get_resampled_pil(light_source, w, h)

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
        mode = "RGBA" if raw.mode in ("RGBA", "LA") or raw.format == "PNG" else "RGB"
        img = raw.convert(mode)
        resampled = img.resize((width, height), Image.Resampling.LANCZOS)
        _PIL_CACHE[cache_key] = resampled
        return resampled


def _load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Attempts to load a Windows TrueType font, falling back to default."""
    try:
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def get_left_branding_banner(width: int, height: int) -> Optional[ctk.CTkImage]:
    """Renders the complete cinematic restaurant branding panel for the left side.

    - Covers the entire panel with restaurant ambience photograph
    - Applies a rich dark obsidian overlay (#0B0B12, 45-60% opacity)
    - Places the RestoPro logo near top-left with strict aspect ratio and 0 rectangular artifact
    - Renders the brand tagline, headline, supporting text, and 3 compact feature highlights
    - Caches by (width, height) for instant subsequent layout calls
    """
    if width < 100 or height < 100:
        return None

    cache_key = ("left_banner", width, height)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    if not AMBIENCE_PATH.exists():
        logger.warning(f"Restaurant ambience image not found at {AMBIENCE_PATH}")
        return None

    try:
        base = Image.open(AMBIENCE_PATH).convert("RGB")
        orig_w, orig_h = base.size
        aspect_target = width / height
        aspect_orig = orig_w / orig_h

        # Center-crop to fill target aspect ratio
        if aspect_orig > aspect_target:
            new_w = int(orig_h * aspect_target)
            left = (orig_w - new_w) // 2
            cropped = base.crop((left, 0, left + new_w, orig_h))
        else:
            new_h = int(orig_w / aspect_target)
            top = (orig_h - new_h) // 2
            cropped = base.crop((0, top, orig_w, top + new_h))

        resized = cropped.resize((width, height), Image.Resampling.LANCZOS)

        # 45-60% dark obsidian overlay (#0B0B12)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        for y in range(height):
            # Alpha gradient: 120 (47%) at top to 160 (63%) at bottom
            alpha = int(120 + (160 - 120) * (y / height))
            draw_ov.line([(0, y), (width, y)], fill=(11, 11, 18, alpha))

        banner = Image.alpha_composite(resized.convert("RGBA"), overlay)

        # RestoPro transparent logo (top-left)
        logo_path = LOGO_TRANSPARENT_PATH if LOGO_TRANSPARENT_PATH.exists() else LOGO_PATH
        if logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
            logo_w = min(int(width * 0.36), 245)
            logo_w = max(logo_w, 190)
            logo_h = int(logo_w * 682 / 1024)
            logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

            pad_x = max(int(width * 0.08), 44)
            curr_y = max(int(height * 0.05), 36)
            banner.alpha_composite(logo_resized, (pad_x, curr_y))
            curr_y += logo_h + 14

            draw = ImageDraw.Draw(banner)
            font_badge = _load_font("segoeuib.ttf", 11)
            font_h1 = _load_font("segoeuib.ttf", 28)
            font_sub = _load_font("segoeui.ttf", 13)
            font_card_title = _load_font("segoeuib.ttf", 12)
            font_card_desc = _load_font("segoeui.ttf", 11)

            # Tagline badge pill
            badge_text = " ✨ RESTAURANT MANAGEMENT PLATFORM "
            bbox = font_badge.getbbox(badge_text)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pill_w = tw + 20
            pill_h = th + 12
            draw.rounded_rectangle(
                [pad_x, curr_y, pad_x + pill_w, curr_y + pill_h],
                radius=pill_h // 2,
                fill=(30, 27, 75, 230),
                outline=(67, 56, 202, 255),
                width=1
            )
            draw.text((pad_x + 10, curr_y + 6), badge_text, font=font_badge, fill=(199, 210, 254))
            curr_y += pill_h + 20

            # Headline
            draw.text((pad_x, curr_y), "A smarter way to", font=font_h1, fill=(245, 245, 247))
            curr_y += 36
            draw.text((pad_x, curr_y), "manage your restaurant.", font=font_h1, fill=(245, 245, 247))
            curr_y += 44

            # Supporting text
            draw.text((pad_x, curr_y), "Manage orders, billing, kitchen operations and", font=font_sub, fill=(192, 192, 206))
            curr_y += 20
            draw.text((pad_x, curr_y), "restaurant performance — all in one place.", font=font_sub, fill=(192, 192, 206))
            curr_y += 36

            # 3 compact feature highlights
            features = [
                ("Real-Time POS Billing", "Fast counter checkout, split bills & thermal receipts."),
                ("Kitchen Display System", "Live ticket coordination between chefs & cashiers."),
                ("Analytics & Audit Trail", "Daily sales tracking, shift closeouts & tax compliance.")
            ]
            card_w = min(width - pad_x * 2, 440)
            card_h = 56
            for title, desc in features:
                draw.rounded_rectangle(
                    [pad_x, curr_y, pad_x + card_w, curr_y + card_h],
                    radius=10,
                    fill=(18, 19, 31, 220),
                    outline=(38, 39, 59, 255),
                    width=1
                )
                # Accent indicator bar (#6657F5)
                draw.rounded_rectangle(
                    [pad_x + 14, curr_y + 14, pad_x + 18, curr_y + card_h - 14],
                    radius=2,
                    fill=(102, 87, 245, 255)
                )
                draw.text((pad_x + 30, curr_y + 10), title, font=font_card_title, fill=(241, 245, 249))
                draw.text((pad_x + 30, curr_y + 30), desc, font=font_card_desc, fill=(161, 161, 181))
                curr_y += card_h + 10

        composited = banner.convert("RGB")
        ctk_img = ctk.CTkImage(
            light_image=composited,
            dark_image=composited,
            size=(width, height)
        )
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img
    except Exception as e:
        logger.error(f"Failed to create left branding banner: {e}")
        return None


def get_ambience_banner(width: int, height: int, is_dark: bool = True) -> Optional[ctk.CTkImage]:
    """Compatibility helper returning the branding banner."""
    return get_left_branding_banner(width, height)


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
            setattr(window, "_icon_photo_ref", photo)
            return True
    except Exception as e:
        logger.debug(f"Notice: OS window icon assignment skipped ({e})")
    return False
