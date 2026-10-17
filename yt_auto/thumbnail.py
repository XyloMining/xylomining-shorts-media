"""1080x1920 JPEG thumbnail (kept < 2 MB, YouTube's limit) with big hook text."""
import pathlib

from PIL import Image, ImageDraw

from .fonts import fit, font, wrap
from .render import draw_chain, hex_rgb, make_bg


def make_thumbnail(cfg, item, out: pathlib.Path) -> pathlib.Path:
    W, H = cfg["video"]["width"], cfg["video"]["height"]
    accent, ff = hex_rgb(cfg["video"]["accent"]), cfg["video"].get("font_path", "")
    img = make_bg(W, H)
    d = ImageDraw.Draw(img, "RGBA")
    draw_chain(d, W, 1250, 0.0, accent, 3)
    th = item["thumbnail"]
    f1, l1, sz1 = fit(th["line1"].upper(), W - 140, 560, 230, 90, ff, max_lines=2)
    y = 380
    for line in l1:
        d.text((W // 2, y), line, font=f1, fill=accent + (255,), anchor="mt")
        y += int(sz1 * 1.1)
    f2, l2, sz2 = fit(th.get("line2", "").upper(), W - 160, 380, 96, 56, ff, max_lines=3)
    y += 40
    for line in l2:
        d.text((W // 2, y), line, font=f2, fill=(255, 255, 255, 255), anchor="mt")
        y += int(sz2 * 1.2)
    d.text((W // 2, 150), cfg["brand"].upper(), font=font(52, ff), fill=(255, 255, 255, 200), anchor="mm")
    rgb = img.convert("RGB")
    for q in (90, 80, 70, 55):
        rgb.save(out, "JPEG", quality=q, optimize=True)
        if out.stat().st_size < 1_900_000:
            break
    return out
