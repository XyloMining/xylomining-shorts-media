"""TikTok Short for the Linkvertise creator campaign (paid promotion). Renders outside the pipeline database.
No earnings claims, no dollar figures. The #ad disclosure is added by the user at the start of the title; the caption also says paid promotion.   python promo/build_linkvertise_short.py"""
import copy, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from yt_auto import config, content, render  # noqa: E402
from yt_auto.render import render_video  # noqa: E402

AFF = "https://linkvertise.com/?affiliate_id=10151711"
ITEM = {
    "topic": "Linkvertise for creators (paid promotion)",
    "hook": "I use Linkvertise on my own referral links.",
    "style": {"bg": "aurora"},
    "scenes": [
        {"text": "Creators do the work", "narration": "Creators put real work into digital content, and not every platform pays for it."},
        {"text": "Ads and subscriptions", "narration": "Linkvertise says creator revenue comes from ad placements and from Linkvertise Premium subscriptions."},
        {"text": "How I use it", "narration": "I use it on my own referral links. I will not quote earnings, because results differ for everyone and can be low."},
        {"text": "Your call", "narration": "If you share links or content, you can try it with the link in my bio."},
    ],
    "cta": "Which links would you share?",
    "title": "Linkvertise for Creators",
    "description_body": "Paid promotion. Linkvertise says creator revenue comes from ad placements and Linkvertise Premium subscriptions. I use it on my own referral links. Results differ for everyone and can be low, and I am not quoting earnings. Try it: " + AFF,
    "tags": ["linkvertise", "creator tools", "link monetization", "paid promotion"],
    "hashtags": ["#ad", "#paidpartnership", "#Linkvertise"],
    "thumbnail": {"line1": "LINKVERTISE", "line2": "FOR CREATORS"},
    "sources": [{"title": "Linkvertise", "url": "https://linkvertise.com"}],
}

if __name__ == "__main__":
    item = copy.deepcopy(ITEM)
    cfg = config.load()
    problems = content.validate(cfg, item)
    if problems:
        sys.exit("Validation failed: " + "; ".join(problems))
    render.draw_chain = lambda *a, **k: None
    print(render_video(cfg, item, ROOT / "promo" / "out" / "linkvertise-tiktok"))
