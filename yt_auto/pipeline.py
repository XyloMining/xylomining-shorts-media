"""Orchestration: keep `buffer_slots` future slots built (script -> narration -> video -> thumbnail), gate them behind
approval, stage approved media in the public GitHub repo, and emit a queue for Metricool.

Scheduling itself happens in the Claude session through the Metricool tools (they are not callable from plain
Python); `queue` prints exactly what to send and `mark-scheduled` records the result."""
import datetime as dt
import json
import pathlib
import shutil
import subprocess

from . import content
from .config import DATA, ROOT, STATE
from .notify import notify
from .render import render_video
from .schedule import from_utc_iso, theme_for, to_utc_iso, upcoming_slots
from .state import DB, topic_hash
from .thumbnail import make_thumbnail
from .util import get_logger

ACTIVE = ("pending_approval", "approved", "staged", "scheduled")


def pause_flag() -> pathlib.Path:
    return STATE / "PAUSED"


def is_paused() -> bool:
    return pause_flag().exists()


def load_insights():
    p = STATE / "insights.json"
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    except json.JSONDecodeError:
        return None


# ----------------------------------------------------------------------------- build
def build_post(cfg, db, slot, root: pathlib.Path):
    log = get_logger()
    item = content.apply_cta(cfg, content.generate(cfg, db, slot, load_insights()))
    problems = content.validate(cfg, item)
    if problems:
        raise RuntimeError(f"content failed validation: {problems}")
    folder = root / slot.strftime("%Y-%m-%d_%H%M")
    folder.mkdir(parents=True, exist_ok=True)
    desc = content.build_description(cfg, item)
    tags = [t for t in item["tags"] if t][:15]
    (folder / "item.json").write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "script.txt").write_text(content.narration_of(item), encoding="utf-8")
    (folder / "meta.json").write_text(json.dumps({"title": item["title"], "description": desc, "tags": tags, "sources": item["sources"],
                                                  "publish_local": slot.isoformat()}, indent=2, ensure_ascii=False), encoding="utf-8")
    r = render_video(cfg, item, folder)
    thumb = make_thumbnail(cfg, item, folder / "thumb.jpg")
    auto = db.manual_approvals() >= cfg["approval"]["required_count"]
    pid = db.insert(slot_utc=to_utc_iso(slot), theme=theme_for(cfg, slot), topic=item["topic"], topic_hash=topic_hash(item["topic"]),
                    status="approved" if auto else "pending_approval", title=item["title"], description=desc, tags=json.dumps(tags),
                    folder=str(folder), video_path=str(r["path"]), thumb_path=str(thumb), approved_by="auto" if auto else None)
    log.info("built post %s for %s (%s, %.1fs, tts=%s)", pid, slot.isoformat(), "auto-approved" if auto else "needs approval", r["seconds"], r["tts"])
    return pid


def reslot_stale(cfg, db, now):
    """Unscheduled rows whose slot is too close or past get the next free slot (content is never wasted)."""
    cutoff = to_utc_iso(now + dt.timedelta(minutes=cfg["pipeline"]["min_lead_minutes"]))
    taken = {r["slot_utc"] for r in db.all()}
    for r in db.by_status("pending_approval", "approved", "staged"):
        if r["slot_utc"] <= cutoff:
            for s in upcoming_slots(cfg, now, 60, cfg["pipeline"]["min_lead_minutes"]):
                u = to_utc_iso(s)
                if u not in taken:
                    get_logger().info("post %s slot %s passed; moved to %s", r["id"], r["slot_utc"], u)
                    db.update(r["id"], slot_utc=u, theme=theme_for(cfg, s))
                    taken.add(u)
                    break


# ----------------------------------------------------------------------------- git / staging
def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def persist(cfg, message="Update pipeline state"):
    """Commit + push state/ and log/ (and anything staged) so the next session starts from the same state."""
    if not cfg["media"]["git_push"]:
        return True
    _git("add", "-A", "state", "log", "videos", "thumbs")
    if _git("diff", "--cached", "--quiet").returncode == 0:
        return True
    r = _git("commit", "-q", "-m", message)
    if r.returncode:
        get_logger().error("git commit failed: %s", r.stderr[-300:])
        return False
    pr = _git("pull", "--rebase", "--autostash", "origin", "main")
    if pr.returncode:
        _git("rebase", "--abort")
        notify("Could not sync with GitHub before pushing", pr.stderr[-400:])
        return False
    p = _git("push", "origin", "HEAD")
    if p.returncode:
        notify("Could not push to GitHub", p.stderr[-400:])
        return False
    return True


def _prune(cfg, db):
    keep = cfg["media"].get("keep_last_videos", 30)
    protected = {pathlib.Path(r["video_url"]).name for r in db.by_status("staged") if r["video_url"]}
    vids = sorted((ROOT / "videos").glob("*.mp4"))
    for v in vids[:-keep] if keep else []:
        if v.name not in protected:
            v.unlink()
            (ROOT / "thumbs" / (v.stem + ".jpg")).unlink(missing_ok=True)


def stage_approved(cfg, db):
    """Copy approved videos into the repo, push, and mark them 'staged' with public URLs."""
    log = get_logger()
    rows = db.by_status("approved")
    if not rows:
        return []
    base = cfg["media"]["raw_base"].rstrip("/")
    staged = []
    for r in rows:
        name = f"{from_utc_iso(r['slot_utc'], cfg):%Y-%m-%d_%H%M}_{r['id']}"
        src = pathlib.Path(r["video_path"]) if r["video_path"] else None
        if src is None or not src.exists():
            db.update(r["id"], status="failed", error="rendered video missing from scratch dir; rebuild needed")
            notify(f"Rendered video missing for post {r['id']}", r["title"])
            continue
        (ROOT / "videos").mkdir(exist_ok=True)
        (ROOT / "thumbs").mkdir(exist_ok=True)
        shutil.copy2(src, ROOT / "videos" / f"{name}.mp4")
        shutil.copy2(r["thumb_path"], ROOT / "thumbs" / f"{name}.jpg")
        ld = ROOT / "log" / name
        ld.mkdir(parents=True, exist_ok=True)
        for f in ("item.json", "meta.json", "script.txt"):
            shutil.copy2(pathlib.Path(r["folder"]) / f, ld / f)
        staged.append((r, name))
    if not staged:
        return []
    if cfg["media"]["git_push"]:
        _prune(cfg, db)
        if not persist(cfg, f"Stage {len(staged)} Short(s) for Metricool"):
            notify("Staging failed: media not pushed", "Videos stay 'approved' and will be retried on the next run.")
            return []
    for r, name in staged:
        db.update(r["id"], status="staged", video_url=f"{base}/videos/{name}.mp4", thumb_url=f"{base}/thumbs/{name}.jpg", error=None)
        log.info("staged post %s -> %s/videos/%s.mp4", r["id"], base, name)
    return [r["id"] for r, _ in staged]


# ----------------------------------------------------------------------------- metricool queue
DONE_COL = {"youtube": "metricool_uuid", "tiktok": "tt_metricool_uuid"}


def _base_info(cfg, r, network, text):
    slot = from_utc_iso(r["slot_utc"], cfg)
    info = {"autoPublish": True, "draft": False, "descendants": [], "firstCommentText": "", "hasNotReadNotes": False,
            "media": [r["video_url"]], "mediaAltText": [], "providers": [{"network": network}],
            "publicationDate": {"dateTime": slot.strftime("%Y-%m-%dT%H:%M:%S"), "timezone": cfg["timezone"]},
            "shortener": False, "smartLinkData": {"ids": []}, "text": text}
    return slot, info


def _log_item(r):
    """The committed log/<name>/item.json written at staging time (available in any later session)."""
    p = ROOT / "log" / pathlib.Path(r["video_url"]).stem / "item.json"
    return json.loads(p.read_text(encoding="utf-8"))


def metricool_info(cfg, r, network="youtube"):
    m = cfg["metricool"]
    if network == "youtube":
        slot, info = _base_info(cfg, r, "youtube", r["description"])
        yt = {"title": r["title"][:100], "type": m["yt_type"], "privacy": m["privacy"], "tags": json.loads(r["tags"]),
              "category": m["category"], "madeForKids": bool(m["made_for_kids"]), "isAiGeneratedContent": bool(m["is_ai_generated_content"])}
        if m.get("notify_subscribers") is not None:
            yt["notifySubscribers"] = bool(m["notify_subscribers"])
        info["youtubeData"] = yt
        if m.get("send_thumbnail") and r["thumb_url"]:
            info["videoThumbnailUrl"] = r["thumb_url"]
    elif network == "tiktok":
        t = cfg["tiktok"]
        slot, info = _base_info(cfg, r, "tiktok", content.build_tiktok_caption(cfg, _log_item(r)))
        info["tiktokData"] = {"disableComment": bool(t["disable_comment"]), "disableDuet": bool(t["disable_duet"]),
                              "disableStitch": bool(t["disable_stitch"]), "privacyOption": t["privacy"],
                              "commercialContentThirdParty": bool(t["commercial_third_party"]),
                              "commercialContentOwnBrand": bool(t["commercial_own_brand"]),
                              "title": r["title"][:90], "autoAddMusic": bool(t["auto_add_music"]), "isAigc": bool(t["is_aigc"])}
    else:
        raise ValueError(f"unsupported network {network}")
    return {"id": r["id"], "network": network, "title": r["title"], "date": slot.isoformat(timespec="seconds"),
            "blogId": m["blog_id"], "info": info}


def queue_items(cfg, db, now=None):
    """One item per (staged post, network) that is not yet scheduled in Metricool."""
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = to_utc_iso(now + dt.timedelta(minutes=5))
    out = []
    for r in db.by_status("staged"):
        if r["slot_utc"] <= cutoff or not r["video_url"]:
            continue
        for net in cfg["metricool"]["networks"]:
            if not r[DONE_COL[net]]:
                out.append(metricool_info(cfg, r, net))
    return out


def mark_scheduled(db, pid, network, metricool_id, uuid, planner_url, cfg=None):
    r = db.get(pid)
    if r is None:
        raise ValueError(f"no post {pid}")
    if r["status"] != "staged":
        raise ValueError(f"post {pid} is '{r['status']}', not 'staged' (refusing, to avoid duplicate scheduling)")
    if network not in DONE_COL:
        raise ValueError(f"unsupported network {network}")
    if r[DONE_COL[network]]:
        raise ValueError(f"post {pid} is already scheduled on {network} (refusing duplicate)")
    cols = ({"metricool_id": str(metricool_id), "metricool_uuid": str(uuid), "planner_url": planner_url} if network == "youtube"
            else {"tt_metricool_id": str(metricool_id), "tt_metricool_uuid": str(uuid), "tt_planner_url": planner_url})
    db.update(pid, error=None, **cols)
    r = db.get(pid)
    nets = (cfg or {}).get("metricool", {}).get("networks", ["youtube"])
    if all(r[DONE_COL[n]] for n in nets):
        db.update(pid, status="scheduled")


# ----------------------------------------------------------------------------- main cycle
def run(cfg, stage=True, now=None):
    log = get_logger()
    now = now or dt.datetime.now(dt.timezone.utc)
    db = DB()
    if is_paused():
        log.info("PAUSED - nothing generated or staged (run `python -m yt_auto resume`).")
        return db
    if db.manual_approvals() >= cfg["approval"]["required_count"]:   # gate passed: the rest need no manual step
        for r in db.by_status("pending_approval"):
            db.update(r["id"], status="approved", approved_by="auto")
    reslot_stale(cfg, db, now)
    root = DATA / "posts"
    taken = {r["slot_utc"] for r in db.all()}
    now_iso = to_utc_iso(now)

    def have():
        return len([r for r in db.all() if r["status"] in ACTIVE and r["slot_utc"] > now_iso])

    made = 0
    for slot in upcoming_slots(cfg, now, cfg["pipeline"]["buffer_slots"] + len(taken) + 5, cfg["pipeline"]["min_lead_minutes"]):
        if have() >= cfg["pipeline"]["buffer_slots"]:
            break
        if to_utc_iso(slot) in taken:
            continue
        try:
            build_post(cfg, db, slot, root)
            made += 1
        except Exception as e:  # noqa: BLE001
            notify(f"Could not build the Short for {slot.strftime('%a %d %b %H:%M')}", str(e))
            break
    n = len(db.by_status("pending_approval"))
    if n:
        notify(f"{n} Short(s) waiting for your approval", "Preview the videos, then run: python -m yt_auto approve all", level="INFO")
    if stage:
        stage_approved(cfg, db)
    return db
