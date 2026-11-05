"""Thumbnail for the join-GoMining Short: generated background + text. python promo/build_join_thumb.py [bg.png]"""
import pathlib, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = pathlib.Path(__file__).resolve().parents[1]
bg = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else R / "promo/thumbs/bg-phone-coin.png"
F = str(R / "assets/Poppins-Bold.ttf")
W, H = 1080, 1920
im = Image.open(bg).convert("RGB")
s = max(W / im.width, H / im.height)
im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
d = ImageDraw.Draw(im)

def text(y, t, size, fill, stroke=10):
    f = ImageFont.truetype(F, size)
    while d.textlength(t, font=f) > W - 100:
        size -= 4
        f = ImageFont.truetype(F, size)
    d.text((W / 2, y), t, font=f, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=(15, 8, 40))

text(250, "JOIN GOMINING", 130, (255, 255, 255))
text(400, "STEP BY STEP", 120, (255, 205, 60))
d.rounded_rectangle((110, 1500, W - 110, 1700), 40, fill=(124, 58, 237), outline=(255, 255, 255), width=6)
text(1565, "PROMO CODE", 56, (255, 255, 255), 0)
text(1640, "WCAZD0T", 100, (255, 255, 255), 0)
out = R / "promo/out/join-gomining/thumbnail.png"
im.save(out)
print(out)
