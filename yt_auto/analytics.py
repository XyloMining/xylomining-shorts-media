"""Weekly report. Metrics come from Metricool (the Claude session fetches them with the Metricool analytics tools and
writes data/metrics.json: a list of rows with at least `title`, plus views / engagedViews / averageViewDuration /
averageViewPercentage / likes / comments / subscribersGained where available).

Not measurable through YouTube's APIs (verified against the metrics reference): description-link clicks and the Studio
'viewed vs swiped away' figure. Funnel numbers come from CSVs you export by hand."""
import csv
import datetime as dt
import json
import pathlib

from .config import REPORTS, ROOT, STATE
from .util import get_logger


def _csv(path):
    p = ROOT / path
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score(m):
    views = m.get("engagedViews") or m.get("views") or 0
    return views * (m.get("averageViewPercentage", 0) / 100) + 20 * m.get("subscribersGained", 0) + m.get("likes", 0) * 2 + m.get("comments", 0) * 3


def weekly_report(cfg, db, today=None, rows=None):
    log = get_logger()
    a = cfg["analytics"]
    today = today or dt.date.today()
    end, start = today - dt.timedelta(days=1), today - dt.timedelta(days=a["lookback_days"])
    posts = [r for r in db.all() if r["status"] in ("scheduled", "published")]
    if rows is None:
        p = ROOT / a["metrics_json"]
        if not p.exists():
            return None
        rows = json.loads(p.read_text(encoding="utf-8"))
    by_title = {r["title"].strip().lower(): r for r in posts}
    rows = [dict(r) for r in rows if r.get("title", "").strip().lower() in by_title]
    if not rows:
        return None
    for r in rows:
        r["score"] = score(r)
    rows.sort(key=lambda r: r["score"], reverse=True)
    lv = {r.get("title", "").lower(): r for r in _csv(a["linkvertise_csv"])}
    rf = {r.get("title", "").lower(): r for r in _csv(a["referrals_csv"])}
    lines = [f"# Weekly report {start} to {end}", "",
             f"Videos with data: {len(rows)} of {len(posts)} tracked. Analytics lag 2-3 days, so the newest videos read low.", "",
             "| Video | Views | Engaged | Avg dur (s) | Avg % | Likes | Comments | Subs | LV visits | Referrals |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        k = r["title"].strip().lower()
        lines.append(f"| {r['title']} | {r.get('views', 0)} | {r.get('engagedViews', 0)} | {r.get('averageViewDuration', 0):.0f} | "
                     f"{r.get('averageViewPercentage', 0):.0f}% | {r.get('likes', 0)} | {r.get('comments', 0)} | {r.get('subscribersGained', 0)} | "
                     f"{lv.get(k, {}).get('visits', 'n/a')} | {rf.get(k, {}).get('referrals', 'n/a')} |")
    top = rows[:a["top_n"]]
    lines += ["", f"## Top {len(top)} (retention-weighted score)", ""]
    insights = []
    for r in top:
        p = by_title[r["title"].strip().lower()]
        item = {}
        try:
            item = json.loads((pathlib.Path(p["folder"]) / "item.json").read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        lines.append(f"- **{p['title']}** (score {r['score']:.0f}, {r.get('averageViewPercentage', 0):.0f}% viewed). Hook: \"{item.get('hook', 'n/a')}\"")
        insights.append({"topic": p["topic"], "hook": item.get("hook"), "avg_view_percentage": round(r.get("averageViewPercentage", 0)), "title": p["title"]})
    lines += ["", "## Not measurable through the API",
              "- Viewed-vs-swiped-away rate: YouTube Studio only. Check it there.",
              "- Description-link clicks: not exposed by YouTube. Export the Linkvertise dashboard to `data/linkvertise.csv` (title,visits,completed).",
              "- GoMining referrals: export to `data/referrals.csv` (title,referrals) if you can attribute them.",
              "", "No video is deleted or re-uploaded automatically; insights only steer future *new* topics."]
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"weekly_{today.isoformat()}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    (STATE / "insights.json").write_text(json.dumps(insights, indent=1), encoding="utf-8")
    log.info("weekly report written: %s", out)
    return out
