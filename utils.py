"""Small drawing helpers shared by image_generator.py and video_generator.py."""
from __future__ import annotations

import random

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES_BOLD = ["arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]
_FONT_CANDIDATES_REGULAR = ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"]


def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    """Return a TrueType font if one is found, otherwise Pillow's built-in font."""
    names = _FONT_CANDIDATES_BOLD if bold else _FONT_CANDIDATES_REGULAR
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Split text into lines that fit inside max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_centered_text(img: Image.Image, text: str, font, max_width_ratio: float = 0.8,
                       fill=(255, 255, 255), center_y: float = 0.5, max_lines: int = 6) -> None:
    """Draw wrapped, centred text with a soft shadow directly on img."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    lines = wrap_text(draw, text, font, int(w * max_width_ratio))[:max_lines]
    if not lines:
        return
    line_h = int(font.size * 1.25) if hasattr(font, "size") else 30
    total_h = line_h * len(lines)
    y = int(h * center_y - total_h / 2)
    for line in lines:
        cx, cy = w / 2, y + line_h / 2
        try:  # anchor="mm" centres the text exactly (needs a TrueType/FreeType font)
            draw.text((cx + 2, cy + 2), line, font=font, fill=(0, 0, 0), anchor="mm")
            draw.text((cx, cy), line, font=font, fill=fill, anchor="mm")
        except (ValueError, TypeError):  # very old bitmap fallback font
            tw = draw.textlength(line, font=font)
            draw.text(((w - tw) / 2 + 2, y + 2), line, font=font, fill=(0, 0, 0))
            draw.text(((w - tw) / 2, y), line, font=font, fill=fill)
        y += line_h


def seeded_palette(seed_text: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    """Two pleasant, repeatable colours derived from text."""
    rng = random.Random(seed_text)
    import colorsys

    def colour(h, s, v):
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)

    h = rng.random()
    return colour(h, 0.65, 0.55), colour((h + 0.18 + rng.random() * 0.15) % 1.0, 0.7, 0.9)


def make_gradient(size: tuple[int, int], c1, c2) -> Image.Image:
    """Diagonal two-colour gradient."""
    w, h = size
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    t = ((x + y) / 2.0)[..., None]
    c1a = np.array(c1, dtype=np.float32)[None, None, :]
    c2a = np.array(c2, dtype=np.float32)[None, None, :]
    arr = (c1a * (1 - t) + c2a * t).astype(np.uint8)
    return Image.fromarray(arr, "RGB")
