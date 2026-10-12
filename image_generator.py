"""Image generation module.

REAL generation : Hugging Face Inference (documented API) via the official
                  `huggingface_hub` library -> InferenceClient.text_to_image().
DEMO placeholder: a locally drawn gradient picture, clearly labelled as NOT AI.
"""
from __future__ import annotations

import hashlib
import io
import os
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFilter

from utils import draw_centered_text, get_font, make_gradient, seeded_palette

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"

# Style name -> text added to the prompt
STYLES: dict[str, str] = {
    "None (use my prompt only)": "",
    "Photorealistic": "photorealistic, highly detailed, natural lighting, sharp focus",
    "Digital Art": "digital art, vibrant colours, detailed illustration, trending on artstation",
    "Anime": "anime style, clean line art, vivid colours, studio quality",
    "Oil Painting": "oil painting, visible brush strokes, rich textures, classical style",
    "Watercolor": "watercolor painting, soft washes, delicate details, paper texture",
    "3D Render": "3D render, soft studio lighting, smooth materials, high detail",
    "Pixel Art": "pixel art, retro 16-bit game style, limited colour palette",
    "Cinematic": "cinematic still, dramatic lighting, shallow depth of field, film grain",
}


class ImageGenerationError(Exception):
    """Raised when the real image API fails (message is safe to show to the user)."""


class MissingCredentialsError(ImageGenerationError):
    """Raised when no Hugging Face token is configured."""


def get_hf_token() -> str | None:
    """Look for the token in environment variables / .env, then in Streamlit secrets."""
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if token and token.strip() and not token.strip().startswith("hf_your_token"):
        return token.strip()
    try:  # Streamlit secrets are optional; any error simply means "not configured"
        import streamlit as st

        value = st.secrets.get("HF_TOKEN")
        if value and str(value).strip() and not str(value).startswith("hf_your_token"):
            return str(value).strip()
    except Exception:
        pass
    return None


def has_credentials() -> bool:
    return get_hf_token() is not None


def get_model_name() -> str:
    return os.getenv("HF_IMAGE_MODEL", "").strip() or DEFAULT_MODEL


def build_prompt(prompt: str, style: str) -> str:
    suffix = STYLES.get(style, "")
    prompt = prompt.strip()
    return f"{prompt}, {suffix}" if suffix else prompt


def _friendly_error(exc: Exception) -> str:
    text = str(exc)
    low = text.lower()
    if "401" in low or "403" in low or "unauthorized" in low or "forbidden" in low:
        return ("Hugging Face rejected the token (unauthorized). Check that HF_TOKEN in your "
                ".env file is correct and has permission to use Inference Providers.")
    if "402" in low or "payment" in low or "credit" in low or "quota" in low:
        return ("Your free Hugging Face usage quota seems to be used up. Wait for it to reset, "
                "or check your account's billing/usage page.")
    if "429" in low or "rate" in low:
        return "Too many requests right now. Please wait a minute and try again."
    if "503" in low or "loading" in low or "timeout" in low or "timed out" in low:
        return "The model is busy or still loading. Please try again in a moment."
    if "connection" in low or "network" in low or "resolve" in low:
        return "Could not reach Hugging Face. Check your internet connection and try again."
    return f"The image service returned an error: {text[:300]}"


def generate_image(prompt: str, style: str) -> Image.Image:
    """REAL AI image generation. Raises MissingCredentialsError / ImageGenerationError."""
    token = get_hf_token()
    if not token:
        raise MissingCredentialsError(
            "No Hugging Face token found. Add HF_TOKEN to your .env file "
            "(see .env.example), or use Demo Mode."
        )
    if not prompt.strip():
        raise ImageGenerationError("Please type a prompt first.")
    try:
        from huggingface_hub import InferenceClient
    except ImportError as exc:
        raise ImageGenerationError(
            "The 'huggingface_hub' package is not installed. Run: pip install -r requirements.txt"
        ) from exc
    try:
        client = InferenceClient(token=token)
        image = client.text_to_image(build_prompt(prompt, style), model=get_model_name())
    except Exception as exc:  # network, auth, quota, model errors
        raise ImageGenerationError(_friendly_error(exc)) from exc
    if not isinstance(image, Image.Image):
        raise ImageGenerationError("The service did not return a valid image.")
    return image.convert("RGB")


def generate_demo_image(prompt: str, style: str, size: tuple[int, int] = (1024, 1024)) -> Image.Image:
    """LOCAL placeholder picture. NOT AI-generated. Labelled as such on the image itself."""
    seed = hashlib.sha256(f"{prompt}|{style}".encode()).hexdigest()
    rng = random.Random(seed)
    c1, c2 = seeded_palette(seed)
    img = make_gradient(size, c1, c2).convert("RGBA")

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = size
    for _ in range(9):
        r = rng.randint(int(w * 0.08), int(w * 0.28))
        x, y = rng.randint(0, w), rng.randint(0, h)
        col = (rng.randint(120, 255), rng.randint(120, 255), rng.randint(120, 255), rng.randint(50, 110))
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    overlay = overlay.filter(ImageFilter.GaussianBlur(max(w, h) // 60))
    img = Image.alpha_composite(img, overlay).convert("RGB")

    draw_centered_text(img, prompt.strip()[:160] or "(empty prompt)", get_font(max(24, w // 20)),
                       max_width_ratio=0.78, center_y=0.47)
    draw_centered_text(img, f"Style: {style}", get_font(max(16, w // 40), bold=False),
                       max_width_ratio=0.8, center_y=0.80, fill=(235, 235, 245))
    banner_h = max(40, h // 12)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, h - banner_h, w, h), fill=(0, 0, 0))
    draw_centered_text(img, "DEMO PLACEHOLDER - NOT an AI-generated image",
                       get_font(max(16, w // 42)), max_width_ratio=0.95,
                       fill=(255, 210, 80), center_y=1 - banner_h / 2 / h, max_lines=1)
    return img


def image_to_png_bytes(image: Image.Image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def save_image(image: Image.Image, prefix: str = "image") -> Path:
    """Save to the outputs folder and return the file path."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"{prefix}_{stamp}.png"
    image.save(path, format="PNG")
    return path
