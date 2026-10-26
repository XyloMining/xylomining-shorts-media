"""One-off Short advertising the website. Renders with the normal Short renderer, outside the pipeline database.
Run from the repo root:  python promo/build_promo.py"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from yt_auto import config, content  # noqa: E402
from yt_auto.render import render_video  # noqa: E402
from yt_auto.thumbnail import make_thumbnail  # noqa: E402

SITE = "https://xylomining.github.io"
ITEM = {
    "topic": "Website promo: xylomining.github.io",
    "hook": "Confused by Bitcoin mining jargon? I built a website for you.",
    "scenes": [
        {"text": "Who it's for", "narration": "It's for anyone curious how Bitcoin mining works, or weighing up digital mining, without the hype."},
        {"text": "Plain English guides", "narration": "Inside are plain English guides on hashrate, difficulty, maintenance fees and mining pools."},
        {"text": "Test your own numbers", "narration": "There's a calculator with growth graphs, so you can test your own assumptions, including the downsides."},
        {"text": "My real results", "narration": "My favourite part is the My results page. It shows my own numbers. They are not typical, and can be lower."},
    ],
    "cta": "Find it at xylomining dot github dot io. Link in my bio. Which page would you open first? Tell me below.",
    "title": "I Built a Website to Explain Bitcoin Mining in Plain English",
    "description_body": "Guides, a calculator with growth graphs, live channel stats and my own results page, all free to read.",
    "tags": ["bitcoin mining", "how bitcoin mining works", "gomining", "mining calculator", "crypto for beginners"],
    "hashtags": ["#Shorts", "#Bitcoin", "#BitcoinMining"],
    "thumbnail": {"line1": "MINING WEBSITE", "line2": "GUIDES + CALCULATOR"},
    "sources": [{"title": "XyloMining", "url": SITE}],
}

if __name__ == "__main__":
    cfg = config.load()
    problems = content.validate(cfg, ITEM)
    if problems:
        sys.exit("Validation failed: " + "; ".join(problems))
    out = ROOT / "promo" / "out" / "website-promo"
    r = render_video(cfg, ITEM, out)
    make_thumbnail(cfg, ITEM, out / "thumb.jpg")
    caption = (f"{ITEM['title']}\n\n{ITEM['description_body']}\n\nWebsite: {SITE}\n(Link in my bio on TikTok and Instagram.)\n"
               "Educational only, not financial advice. Mining results vary and can be negative.\n\n" + " ".join(ITEM["hashtags"]))
    (out / "caption.txt").write_text(caption, encoding="utf-8")
    (out / "item.json").write_text(json.dumps(ITEM, indent=2), encoding="utf-8")
    print(f"Video: {r['path']} ({r['seconds']:.1f}s)\nThumbnail: {out / 'thumb.jpg'}\nCaption: {out / 'caption.txt'}")
