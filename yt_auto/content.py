"""Content generation: script + title + description + tags + thumbnail text.

Backends (config.yaml llm.backend):
  file          FREE   pre-written items in content_bank/*.json (written by Claude in chat)
  claude_cli    `claude -p` on this PC
  anthropic_api Anthropic Messages API (ANTHROPIC_API_KEY, pay-per-use)
  gemini        Google Gemini API (GEMINI_API_KEY, free tier with rate limits)
Whatever the backend, every item passes the same validator before it can be used.
"""
import datetime as dt
import json
import os
import pathlib
import re
import subprocess

import requests

from .config import BANK, DATA, FACTS
from .schedule import theme_for
from .util import get_logger, retry

SCHEMA_EXAMPLE = {
    "day": "monday",
    "topic": "Why Bitcoin blocks take about ten minutes",
    "hook": "Bitcoin never speeds up, even when more miners join.",
    "scenes": [
        {"text": "Blocks every ~10 min", "stat": "10 min", "narration": "The network aims for one block roughly every ten minutes."},
        {"text": "Difficulty adjusts", "narration": "Every 2,016 blocks, about two weeks, difficulty resets to keep that pace."},
    ],
    "cta": "Curious how digital mining works? There's a link in my description.",
    "title": "Why Bitcoin Blocks Always Take ~10 Minutes",
    "description_body": "Bitcoin's difficulty adjustment keeps block time near ten minutes no matter how many miners join.",
    "tags": ["bitcoin", "bitcoin mining", "difficulty adjustment"],
    "hashtags": ["#Shorts", "#Crypto"],
    "thumbnail": {"line1": "10 MINUTES", "line2": "WHY BITCOIN NEVER SPEEDS UP"},
    "sources": [{"title": "Bitcoin developer guide: mining", "url": "https://bitcoin.org/en/developer-guide#mining"}],
}


# ----------------------------------------------------------------------------- prompt
def build_prompt(cfg, slot: dt.datetime, theme: str, past_topics, insights=None) -> str:
    facts = (FACTS / "facts.md").read_text(encoding="utf-8") if (FACTS / "facts.md").exists() else ""
    personal = cfg.get("personal_results") or "NONE PROVIDED - make no claims about the creator's own results."
    hints = ""
    if insights:
        hints = "\nWhat performed best recently (use as inspiration for angle/pacing, never copy):\n" + json.dumps(insights, indent=1)
    return f"""You write one original YouTube Short for the channel "{cfg['brand']}" (educational Bitcoin mining content).
Slot: {slot.strftime('%A %d %B %Y')} - theme: "{theme}".

HARD RULES
- Educational first: the viewer must learn one concrete takeaway even if they never click anything.
- Only make factual claims that appear in the FACT SHEET below. No other numbers, prices, or platform features.
- Never promise or imply profits, guaranteed or typical returns, scarcity or urgency.
- Do not invent testimonials or personal results. Personal results you may mention: {personal}
- Narration total {cfg['content_rules']['min_words']}-{cfg['content_rules']['max_words']} words (about 20-40 seconds spoken).
- hook: <= 14 words, grabs attention in 2 seconds, honest (no clickbait that the video does not deliver).
- 3-5 scenes. Each scene: "text" (on-screen headline, <= 6 words), optional "stat" (a short big figure drawn from the fact sheet), "narration".
- cta: one natural spoken sentence pointing to the description link. Vary it; never pushy. Do NOT say the URL aloud.
- title: <= 70 chars, specific and honest. description_body: 1-3 sentences summarising the lesson (the link, disclosure and hashtags are added by code).
- thumbnail.line1 <= 3 words (big), line2 <= 6 words.
- sources: 1-3 entries with real https URLs taken from the FACT SHEET.
- ENGAGEMENT (without breaking the rules above): open with a tension or curiosity hook (a myth, a surprising number from the fact sheet, or a direct question to the viewer) that the video pays off by the last scene.
  Put the surprise in scene 1, not at the end. Include one "catch" or "the honest part" beat mid-way, since contrast holds attention. Write short, spoken sentences addressed to "you".
  Use a stat on at least one scene. Finish with ONE comment-inviting question the viewer can answer in a few words ("Which one surprised you?"), joined to the description-link sentence in the cta.
  No fake urgency, no "wait for it" or "you won't believe" filler, and the hook must be true.
- Do not repeat these past topics: {json.dumps(list(past_topics)[-40:])}
{hints}

FACT SHEET
{facts}

Return ONLY a JSON object, no markdown fence, matching this example shape exactly:
{json.dumps(SCHEMA_EXAMPLE, indent=1)}
"""


def bank_prompt(cfg, count: int) -> str:
    """Prompt to paste into Claude chat once to fill the free file bank with `count` items."""
    days = "\n".join(f"- {d}: {v['theme']}" for d, v in cfg["schedule"].items())
    base = build_prompt(cfg, dt.datetime.now(), "(see per-day themes)", [])
    base = base.split("Return ONLY")[0]
    return (f"{base}\nWrite {count} DIFFERENT items covering the weekly themes below (rotate evenly, set the matching \"day\" field):\n{days}\n\n"
            f"Return ONLY a JSON array of {count} objects, each matching this shape:\n{json.dumps(SCHEMA_EXAMPLE, indent=1)}\n")


# ----------------------------------------------------------------------------- backends
def _claude_cli(cfg, prompt):
    r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=cfg["llm"]["timeout_seconds"])
    if r.returncode:
        raise RuntimeError(f"claude cli failed: {r.stderr[:300]}")
    return r.stdout


def _anthropic(cfg, prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=cfg["llm"]["timeout_seconds"],
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json={"model": cfg["llm"]["anthropic_model"], "max_tokens": 2000,
                            "messages": [{"role": "user", "content": prompt}]})
    if r.status_code >= 400:
        raise RuntimeError(f"anthropic http {r.status_code}: {r.text[:300]}")
    return "".join(b.get("text", "") for b in r.json()["content"])


def _gemini(cfg, prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{cfg['llm']['gemini_model']}:generateContent"
    r = requests.post(url, params={"key": key}, timeout=cfg["llm"]["timeout_seconds"],
                      json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}})
    if r.status_code >= 400:
        raise RuntimeError(f"gemini http {r.status_code}: {r.text[:300]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0], default=-1)
    if start < 0:
        raise ValueError("no JSON found in model output")
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


# ----------------------------------------------------------------------------- validation
def narration_of(item) -> str:
    return " ".join([item["hook"], *[s["narration"] for s in item["scenes"]], item["cta"]])


def validate(cfg, item) -> list:
    """Return a list of problems (empty list = OK)."""
    rules, p = cfg["content_rules"], []
    try:
        for k in ("topic", "hook", "scenes", "cta", "title", "description_body", "tags", "thumbnail", "sources"):
            if not item.get(k):
                p.append(f"missing field: {k}")
        if p:
            return p
        if not (3 <= len(item["scenes"]) <= 6):
            p.append("need 3-6 scenes")
        for i, s in enumerate(item["scenes"]):
            if not s.get("text") or not s.get("narration"):
                p.append(f"scene {i} needs text and narration")
            elif len(s["text"].split()) > 8:
                p.append(f"scene {i} headline too long")
        words = len(narration_of(item).split())
        if not rules["min_words"] <= words <= rules["max_words"]:
            p.append(f"narration is {words} words; need {rules['min_words']}-{rules['max_words']}")
        if len(item["hook"].split()) > 16:
            p.append("hook too long")
        if len(item["title"]) > 100:
            p.append("title > 100 chars")
        if "http" in item["cta"].lower() or "www." in item["cta"].lower():
            p.append("cta must not contain a URL")
        if not item["sources"] or not all(str(s.get("url", "")).startswith("https://") for s in item["sources"]):
            p.append("sources need https URLs")
        blob = json.dumps(item, ensure_ascii=False).lower()
        for bad in cfg.get("banned_phrases", []):
            if bad.lower() in blob:
                p.append(f"banned phrase: '{bad}'")
        if not rules.get("allow_dollar_figures", False):
            pr = str(cfg.get("personal_results") or "")
            for m in re.findall(r"\$\s?\d[\d,]*(?:\.\d+)?", blob):
                if m.replace(" ", "") not in pr:
                    p.append(f"dollar figure {m} is not in personal_results (set content_rules.allow_dollar_figures)")
                    break
        if not str(item.get("thumbnail", {}).get("line1", "")).strip():
            p.append("thumbnail.line1 missing")
    except (KeyError, TypeError, AttributeError) as e:
        p.append(f"malformed item: {e}")
    return p


def apply_cta(cfg, item):
    """Swap the generic 'in my description' wording for the configured CTA location (cta.where)."""
    where = cfg.get("cta", {}).get("where", "in my description")
    item = dict(item)
    item["cta"] = re.sub(r"in my description", where, item["cta"], flags=re.I)
    return item


def build_tiktok_caption(cfg, item) -> str:
    """Short TikTok caption: no URL (not clickable), honest disclosure, a few hashtags (never #Shorts)."""
    t = cfg["tiktok"]
    tags = []
    for h in [*cfg["description"].get("always_hashtags", []), *item.get("hashtags", [])]:
        h = h if h.startswith("#") else "#" + h
        if h.lower() != "#shorts" and h.lower() not in [x.lower() for x in tags]:
            tags.append(h)
    tags = tags[:t.get("max_hashtags", 5)]
    return f"{item['title']}\n\n{item['description_body'].strip()}\n\n{t['cta_line']}\n{t['disclosure']}\n\n{' '.join(tags)}"[:2100]


def build_description(cfg, item) -> str:
    d = cfg["description"]
    src = "\n".join(f"- {s.get('title', 'Source')}: {s['url']}" for s in item["sources"])
    tags = []
    for h in [*d.get("always_hashtags", []), *item.get("hashtags", [])]:
        h = h if h.startswith("#") else "#" + h
        if h.lower() not in [t.lower() for t in tags]:
            tags.append(h)
    tags = tags[:5]  # YouTube ignores all hashtags if more than 15; keep it tidy
    return (f"{item['description_body'].strip()}\n\n{d['cta_header']}\n{cfg['link']}\n\n{d['disclosure']}\n\n"
            f"Sources:\n{src}\n\n{' '.join(tags)}")[:4900]


# ----------------------------------------------------------------------------- generation
def _bank_items():
    out = []
    for f in sorted(BANK.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            get_logger().error("bad JSON in %s: %s", f, e)
            continue
        out.extend(data if isinstance(data, list) else [data])
    return out


def bank_remaining(cfg, db):
    return [i for i in _bank_items() if not db.is_duplicate_topic(i.get("topic", "")) and not validate(cfg, i)]


def generate(cfg, db, slot, insights=None):
    """Return a validated item for this slot or raise RuntimeError."""
    log = get_logger()
    theme = theme_for(cfg, slot)
    backend = cfg["llm"]["backend"]
    day = slot.strftime("%A").lower()

    if backend in ("file", "file+gemini"):
        pool = bank_remaining(cfg, db)
        for i in pool:  # prefer an item written for this weekday
            if i.get("day") == day:
                return i
        if pool:
            log.warning("no unused '%s' item in content_bank; using another day's item", day)
            return pool[0]
        if backend == "file":
            raise RuntimeError(f"content_bank is empty/used up (need an unused item for {day}). Run: python -m yt_auto bank-prompt")
        log.warning("content bank used up - falling back to Gemini for %s", day)
        backend = "gemini"

    fn = {"claude_cli": _claude_cli, "anthropic_api": _anthropic, "gemini": _gemini}[backend]
    feedback, last = "", []
    for attempt in range(1, cfg["pipeline"]["generation_attempts"] + 1):
        prompt = build_prompt(cfg, slot, theme, db.past_topics(), insights) + feedback
        try:
            item = parse_json(retry(lambda: fn(cfg, prompt), tries=3, base=5, what=f"{backend} call"))
            if isinstance(item, list):
                item = item[0]
        except Exception as e:  # noqa: BLE001
            last = [str(e)]
            log.warning("generation attempt %d failed: %s", attempt, e)
            continue
        last = validate(cfg, item)
        if db.is_duplicate_topic(item.get("topic", "")):
            last.append("topic duplicates an earlier video; choose a different topic")
        if not last:
            return item
        log.warning("attempt %d rejected: %s", attempt, last)
        feedback = "\n\nYour previous answer was rejected for: " + "; ".join(last) + ". Fix these and return the full JSON again."
    raise RuntimeError(f"could not generate valid content: {last}")
