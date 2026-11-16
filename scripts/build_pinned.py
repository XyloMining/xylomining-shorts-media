"""Rebuild pinned posts (ids = the user's schedule numbers). Usage: python scripts/build_pinned.py [--only 61,64]"""
import json, sys, datetime as dt, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from yt_auto import config, content, pipeline
from yt_auto.state import DB
from yt_auto.schedule import slot_for_date
from yt_auto.config import DATA
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pinned_items import ITEMS

cfg = config.load()
bank = {i["title"]: i for i in content._bank_items()}
def reuse(no, date, day, old_title, new_title, topic, hook=None):
    it = dict(bank[old_title]); it.update(no=no, date=date, day=day, title=new_title, topic=topic)
    if hook: it["hook"] = hook
    return it
REUSED = [
 reuse(66, "2026-12-23", "wednesday", "Myth: All 21 Million Bitcoin Can Be Mined", "Myth: All 21 Million Bitcoin Can Be Mined", "Myth: all 21 million bitcoin can be mined (moved to 23 Dec)"),
 reuse(70, "2026-12-27", "sunday", "Year-End Recap: 4 Bitcoin Mining Ideas", "Year-End Recap: 4 Bitcoin Mining Lessons", "Year-end recap: four mining lessons", "Year-end recap: four lessons to take into the new year."),
 reuse(73, "2026-12-30", "wednesday", "3 Mining Numbers to Check Before Year End", "3 Mining Numbers to Check Before 2027", "Three mining numbers to check before 2027", "Three things decide mining results. Check them before 2027."),
 reuse(74, "2026-12-31", "thursday", "Digital Miner Year-End Checklist", "Digital Miner Year-End Portfolio Checklist", "Year-end portfolio checklist for digital miners", "Own digital miners? Do this year-end portfolio check."),
]
for r in REUSED:
    r["scenes"] = [dict(s) for s in r["scenes"]]
items = sorted(ITEMS + REUSED, key=lambda x: x["no"])
only = None
if "--only" in sys.argv: only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
db = DB()
for it in items:
    if only and it["no"] not in only: continue
    slot = slot_for_date(cfg, dt.date.fromisoformat(it["date"]))
    old = db.get(it["no"])
    if old is not None:
        db.con.execute("DELETE FROM posts WHERE id=?", (it["no"],)); db.con.commit()
    clash = db.by_slot(pipeline.to_utc_iso(slot))
    if clash is not None:
        print("slot already used by", clash["id"], clash["title"]); sys.exit(1)
    content.generate = lambda cfg_, db_, slot_, insights=None, _it=it: _it
    pid = pipeline.build_post(cfg, db, slot, DATA / "posts")
    db.con.execute("UPDATE posts SET id=? WHERE id=?", (it["no"], pid)); db.con.commit()
    print("built", it["no"], slot.isoformat(), it["title"])
