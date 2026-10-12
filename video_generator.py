"""Video module.

IMPORTANT / HONESTY NOTE
------------------------
This project does NOT include a genuine AI text-to-video provider. Reliable text-to-video
APIs are paid, change often, and cannot be verified without an account. So the only mode
implemented here is a clearly labelled DEMO: a slideshow MP4 made on your own computer from
text cards (or images you upload) with zoom + cross-fade transitions and optional offline
narration. It is NOT AI video generation, and every frame carries a watermark saying so.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from utils import draw_centered_text, get_font, make_gradient, seeded_palette

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

REAL_VIDEO_AVAILABLE = False  # No genuine text-to-video API is integrated in this project.
WATERMARK = "DEMO MODE - slideshow, NOT AI-generated video"

ProgressCallback = Callable[[float, str], None]


class VideoGenerationError(Exception):
    """Raised with a message that is safe to show to the user."""


@dataclass
class VideoResult:
    path: Path
    duration_seconds: float
    scenes: int
    narrated: bool
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- scenes & slides
def split_into_scenes(prompt: str, max_scenes: int = 6) -> list[str]:
    """Break a prompt into short captions (one per slide)."""
    text = prompt.strip()
    parts = [p.strip() for p in re.split(r"[.!?;\n]+", text) if p.strip()]
    if len(parts) < 2:
        comma_parts = [p.strip() for p in re.split(r",\s+|\s+and then\s+|\s+then\s+", text) if p.strip()]
        if len(comma_parts) > 1:
            parts = comma_parts
    if not parts:
        parts = [text or "Demo video"]
    return parts[:max_scenes]


def _add_watermark(img: Image.Image) -> None:
    w, h = img.size
    band = max(34, h // 18)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, h - band, w, h), fill=(0, 0, 0))
    draw_centered_text(img, WATERMARK, get_font(max(14, h // 40)), max_width_ratio=0.95,
                       fill=(255, 210, 80), center_y=1 - band / 2 / h, max_lines=1)


def _text_slide(caption: str, index: int, size: tuple[int, int]) -> Image.Image:
    c1, c2 = seeded_palette(f"{caption}-{index}")
    img = make_gradient(size, c1, c2)
    draw_centered_text(img, caption, get_font(max(28, size[1] // 12)), max_width_ratio=0.8)
    _add_watermark(img)
    return img


def _image_slide(src: Image.Image, caption: str, size: tuple[int, int]) -> Image.Image:
    """Fit an uploaded picture to the video size (cover/crop) and add a caption."""
    w, h = size
    src = src.convert("RGB")
    scale = max(w / src.width, h / src.height)
    resized = src.resize((max(w, int(src.width * scale)), max(h, int(src.height * scale))))
    left, top = (resized.width - w) // 2, (resized.height - h) // 2
    img = resized.crop((left, top, left + w, top + h))
    if caption:
        draw = ImageDraw.Draw(img, "RGBA")
        draw.rectangle((0, int(h * 0.68), w, int(h * 0.92)), fill=(0, 0, 0, 140))
        draw_centered_text(img, caption, get_font(max(22, h // 18)), max_width_ratio=0.85,
                           center_y=0.80, max_lines=3)
    _add_watermark(img)
    return img


def _frame(base: Image.Image, progress: float, size: tuple[int, int]) -> Image.Image:
    """Slow zoom-in ('Ken Burns') effect. progress goes 0.0 -> 1.0."""
    zoom = 1.0 + 0.08 * progress
    bw, bh = base.size
    cw, ch = bw / zoom, bh / zoom
    box = ((bw - cw) / 2, (bh - ch) / 2, (bw + cw) / 2, (bh + ch) / 2)
    return base.resize(size, Image.BILINEAR, box=box)


# ---------------------------------------------------------------- narration (optional)
def _make_narration(text: str, wav_path: Path) -> float:
    """Offline text-to-speech with pyttsx3 (Windows SAPI5). Returns duration in seconds."""
    import pyttsx3  # imported here so the app still starts if it is missing

    engine = pyttsx3.init()
    engine.save_to_file(text, str(wav_path))
    engine.runAndWait()
    if not wav_path.exists() or wav_path.stat().st_size == 0:
        raise RuntimeError("The text-to-speech engine did not create an audio file.")
    with wave.open(str(wav_path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def _mux_audio(video_path: Path, wav_path: Path, out_path: Path, duration: float) -> None:
    import imageio_ffmpeg

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(video_path), "-i", str(wav_path),
           "-c:v", "copy", "-af", "apad", "-c:a", "aac", "-t", f"{duration:.3f}", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-300:] or "ffmpeg failed while adding audio.")


# ---------------------------------------------------------------- main entry point
def create_demo_video(
    prompt: str,
    images: Sequence[Image.Image] | None = None,
    seconds_per_scene: float = 3.0,
    narration: bool = False,
    fps: int = 24,
    size: tuple[int, int] = (1280, 720),
    progress: ProgressCallback | None = None,
) -> VideoResult:
    """Create a DEMO slideshow MP4 (not AI-generated). Returns a VideoResult."""
    if not prompt.strip():
        raise VideoGenerationError("Please type a prompt first.")

    def report(frac: float, msg: str) -> None:
        if progress:
            progress(min(max(frac, 0.0), 1.0), msg)

    warnings: list[str] = []
    captions = split_into_scenes(prompt)
    images = list(images or [])
    n_scenes = max(len(captions), len(images)) if images else len(captions)
    if images and len(captions) < n_scenes:  # reuse the full prompt as caption for extra pictures
        captions += [prompt.strip()] * (n_scenes - len(captions))

    # Optional narration first, so slides can be stretched to fit the speech.
    wav_path: Path | None = None
    if narration:
        report(0.02, "Creating narration (offline text-to-speech)...")
        try:
            tmp_dir = Path(tempfile.mkdtemp(prefix="aics_"))
            wav_path = tmp_dir / "narration.wav"
            speech_len = _make_narration(". ".join(captions[:n_scenes]), wav_path)
            seconds_per_scene = max(seconds_per_scene, (speech_len + 0.8) / n_scenes)
        except Exception as exc:
            wav_path = None
            warnings.append(f"Narration was skipped: {exc}")

    # Build slides (a bit larger than output is not needed; zoom crops from the base image).
    report(0.05, "Preparing slides...")
    bases: list[Image.Image] = []
    for i in range(n_scenes):
        if i < len(images):
            bases.append(_image_slide(images[i], captions[i], size))
        else:
            bases.append(_text_slide(captions[i], i, size))

    OUTPUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    silent_path = OUTPUT_DIR / f"demo_video_{stamp}_silent.mp4"
    final_path = OUTPUT_DIR / f"demo_video_{stamp}.mp4"

    frames_per_scene = max(int(fps * seconds_per_scene), fps)
    transition_frames = int(fps * 0.7)
    total = n_scenes * frames_per_scene + (n_scenes - 1) * transition_frames
    done = 0

    try:
        writer = imageio.get_writer(str(silent_path), fps=fps, codec="libx264",
                                    pixelformat="yuv420p", macro_block_size=1, quality=7)
    except Exception as exc:
        raise VideoGenerationError(
            "Could not start the video encoder. Make sure 'imageio-ffmpeg' is installed "
            f"(pip install -r requirements.txt). Details: {exc}"
        ) from exc

    try:
        for i, base in enumerate(bases):
            for k in range(frames_per_scene):
                writer.append_data(np.asarray(_frame(base, k / frames_per_scene, size)))
                done += 1
                if done % 12 == 0:
                    report(0.1 + 0.8 * done / total, f"Rendering scene {i + 1} of {n_scenes}...")
            if i < n_scenes - 1:  # cross-fade into the next scene
                end_a = _frame(base, 1.0, size)
                start_b = _frame(bases[i + 1], 0.0, size)
                for t in range(transition_frames):
                    blended = Image.blend(end_a, start_b, (t + 1) / (transition_frames + 1))
                    writer.append_data(np.asarray(blended))
                    done += 1
    except Exception as exc:
        raise VideoGenerationError(f"Video rendering failed: {exc}") from exc
    finally:
        writer.close()

    narrated = False
    if wav_path is not None:
        report(0.93, "Adding narration to the video...")
        try:
            _mux_audio(silent_path, wav_path, final_path, total / fps)
            silent_path.unlink(missing_ok=True)
            narrated = True
        except Exception as exc:
            warnings.append(f"Could not add narration audio: {exc}")
    if not narrated:
        silent_path.replace(final_path)

    report(1.0, "Done.")
    return VideoResult(path=final_path, duration_seconds=total / fps, scenes=n_scenes,
                       narrated=narrated, warnings=warnings)
