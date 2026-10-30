"""Short: how to join GoMining, step by step. Renders with the normal Short renderer, outside the pipeline database.
Screens live in promo/shots/gomining/ (9:16 or any phone screenshot). A scene uses its picture only if the file exists,
so the video can be rendered as a draft and re-rendered after you add the recordings.   python promo/build_join_guide.py"""
import copy
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from yt_auto import config, content, render  # noqa: E402
from yt_auto.render import render_video  # noqa: E402

SHOTS = ROOT / "promo" / "shots" / "gomining"
ITEM = {
    "topic": "How to join GoMining, step by step",
    "hook": "Here's how to join GoMining, step by step.",
    "style": {"bg": "aurora"},
    "scenes": [
        {"text": "1. Start from my link", "narration": "Open my GoMining link first, so the new user bonuses attach when you sign up.", "shot": "1-link"},
        {"text": "2. Create your account", "narration": "Create your account and follow the prompts. Features depend on your region.", "shot": "2-signup"},
        {"text": "3. Know your bonuses", "narration": "New users can get five percent bonus mining power on a first miner, up to twenty five TH, plus a month of Platinum Plus. Each bonus has a time window.", "shot": "3-bonuses"},
        {"text": "4. Check before you buy", "narration": "Before buying, read the miner's TH, efficiency and maintenance fee, and test the numbers in my calculator. Returns can be negative.", "shot": "4-miner"},
    ],
    "cta": "My link is on my channel page, and I may earn a benefit if you join. Which step next?",
    "title": "How to Join GoMining: Step by Step",
    "description_body": "A step by step walkthrough of joining GoMining from a referral link, what new users can get, and what to check before you buy. Terms can change, so check GoMining for the current ones.",
    "tags": ["gomining", "how to join gomining", "gomining referral", "bitcoin mining for beginners", "gomining tutorial"],
    "hashtags": ["#Shorts", "#Bitcoin", "#GoMining"],
    "thumbnail": {"line1": "JOIN GOMINING", "line2": "STEP BY STEP"},
    "sources": [{"title": "GoMining: Become a True GoMining Partner", "url": "https://gomining.com/blog/gomining-partner"},
                {"title": "XyloMining quickstart guide", "url": "https://xylomining.github.io/guides/gomining-quickstart/"}],
}

if __name__ == "__main__":
    item = copy.deepcopy(ITEM)
    have, missing = [], []
    for sc in item["scenes"]:
        f = next(iter(sorted(SHOTS.glob(sc["shot"] + ".*"))), None)
        (have if f else missing).append(sc["shot"])
        if f:
            sc["image"] = str(f)
        del sc["shot"]
    cfg = config.load()
    problems = content.validate(cfg, item)
    if problems:
        sys.exit("Validation failed: " + "; ".join(problems))
    render.draw_chain = lambda *a, **k: None  # no block chain behind the hook and call to action
    r = render_video(cfg, item, ROOT / "promo" / "out" / "join-gomining")
    print("screens used:", have, "| still missing:", missing)
    print(r)
