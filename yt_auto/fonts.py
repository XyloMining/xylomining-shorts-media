import functools
import pathlib

from PIL import ImageFont

from .config import ROOT

CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/calibrib.ttf",
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


@functools.lru_cache(maxsize=None)
def font(size: int, path: str = ""):
    for p in ([path] if path else []) + CANDIDATES:
        if not p:
            continue
        q = pathlib.Path(p)
        q = q if q.is_absolute() else ROOT / q
        if q.exists():
            return ImageFont.truetype(str(q), size)
    return ImageFont.load_default()


def wrap(draw_font, text, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw_font.getlength(t) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(text, max_w, max_h, start, minimum=48, path="", max_lines=3, spacing=1.12):
    """Largest font size (<= start) whose wrapped text fits in max_w x max_h within max_lines."""
    size = start
    while size >= minimum:
        f = font(size, path)
        lines = wrap(f, text, max_w)
        if len(lines) <= max_lines and len(lines) * size * spacing <= max_h and all(f.getlength(l) <= max_w for l in lines):
            return f, lines, size
        size -= 4
    f = font(minimum, path)
    return f, wrap(f, text, max_w)[:max_lines], minimum
