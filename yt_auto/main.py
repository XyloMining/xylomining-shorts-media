import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.request

from . import config, content, pipeline
from .notify import notify
from .schedule import from_utc_iso, upcoming_slots
from .state import DB
from .util import Locked, RunLock, get_logger

KOKORO = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


def cmd_setup(cfg, a):
    """Download the free offline narration model (350 MB) if it is missing."""
    d = config.ROOT / cfg["tts"]["kokoro_model_dir"]
    d.mkdir(parents=True, exist_ok=True)
    for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        if (d / f).exists():
            print(f"have {f}")
            continue
        print(f"downloading {f} ...")
        urllib.request.urlretrieve(KOKORO + f, d / f)
    print("setup complete. Also run: pip install -r requirements.txt")


def cmd_doctor(cfg, a):
    ok = True

    def chk(label, cond, hint=""):
        nonlocal ok
        print(f"[{'OK ' if cond else 'FAIL'}] {label}" + ("" if cond else f"  -> {hint}"))
        ok &= bool(cond)

    chk("ffmpeg + ffprobe", shutil.which("ffmpeg") and shutil.which("ffprobe"), "install FFmpeg")
    from .fonts import font
    chk("bold font found", getattr(font(40, cfg["video"].get("font_path", "")), "path", None) is not None, "set video.font_path")
    d = config.ROOT / cfg["tts"]["kokoro_model_dir"]
    chk("Kokoro narration model", (d / "kokoro-v1.0.onnx").exists() and (d / "voices-v1.0.bin").exists(), "run: python -m yt_auto setup")
    try:
        import kokoro_onnx, soundfile  # noqa: F401,E401
        chk("kokoro-onnx + soundfile installed", True)
    except ImportError:
        chk("kokoro-onnx + soundfile installed", False, "pip install -r requirements.txt")
    git = subprocess.run(["git", "remote", "-v"], cwd=config.ROOT, capture_output=True, text=True).stdout
    chk("git remote configured (media hosting)", "github.com" in git, "clone the XyloMining/xylomining-shorts-media repo")
    be = cfg["llm"]["backend"]
    if be in ("file", "file+gemini"):
        n = len(content.bank_remaining(cfg, DB()))
        need = cfg["pipeline"]["buffer_slots"]
        if be == "file+gemini":
            chk(f"content bank: {n} unused items; Gemini key for fallback", n >= need or os.environ.get("GEMINI_API_KEY"),
                "add GEMINI_API_KEY (repo secret / .env) or ask Claude to write more bank items")
        else:
            chk(f"content bank: {n} unused valid items (need >= {need})", n >= need, "ask Claude to write more items: python -m yt_auto bank-prompt 30")
    chk("alert channel (Discord/email) - optional", any(os.environ.get(k) for k in ("DISCORD_WEBHOOK_URL", "NOTIFY_EMAIL_TO")), "alerts still go to logs/alerts.log")
    print("Paused:", pipeline.is_paused())
    return 0 if ok else 1


def cmd_status(cfg, a):
    db = DB()
    print(f"{'id':>3}  {'slot (local)':<17} {'status':<17} title")
    for r in db.all():
        s = from_utc_iso(r["slot_utc"], cfg).strftime("%a %d %b %H:%M")
        print(f"{r['id']:>3}  {s:<17} {r['status']:<17} {r['title']}  {r['planner_url'] or ''}  {('ERR: ' + r['error']) if r['error'] else ''}")
    print("\nNext slots:", ", ".join(s.strftime("%a %d %b %H:%M") for s in upcoming_slots(cfg, dt.datetime.now(dt.timezone.utc), 4)))
    print("PAUSED" if pipeline.is_paused() else "running")


def cmd_run(cfg, a):
    try:
        with RunLock():
            pipeline.run(cfg, stage=not a.no_stage)
            pipeline.persist(cfg, "Update pipeline state")
    except Locked as e:
        get_logger().info("skipping: %s", e)


def cmd_approve(cfg, a):
    db = DB()
    rows = db.by_status("pending_approval") if a.target == "all" else [db.get(int(a.target))]
    for r in rows:
        if r and r["status"] == "pending_approval":
            db.update(r["id"], status="approved", approved_by="manual")
            print(f"approved {r['id']}: {r['title']}")
    print("Next: python -m yt_auto run  (stages approved videos), then python -m yt_auto queue")


def cmd_reject(cfg, a):
    DB().update(a.id, status="rejected")
    print(f"rejected {a.id}. Its topic stays blocked; `run` will build a replacement for the slot.")


def cmd_pause(cfg, a):
    pipeline.pause_flag().write_text(dt.datetime.now().isoformat())
    pipeline.persist(cfg, "Pause publishing")
    print("Paused: no new videos will be generated or staged.\nPosts ALREADY scheduled in Metricool still go out. Ask Claude to 'hold all scheduled posts' to turn them into drafts.")


def cmd_resume(cfg, a):
    pipeline.pause_flag().unlink(missing_ok=True)
    pipeline.persist(cfg, "Resume publishing")
    print("Resumed. Ask Claude to re-schedule any posts it held as drafts.")


def cmd_queue(cfg, a):
    items = pipeline.queue_items(cfg, DB())
    out = config.DATA / "queue.json"
    out.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"\n# {len(items)} post(s) ready to schedule in Metricool (saved to {out})", file=sys.stderr)


def cmd_mark_scheduled(cfg, a):
    pipeline.mark_scheduled(DB(), a.id, a.metricool_id, a.uuid, a.url)
    pipeline.persist(cfg, f"Mark post {a.id} scheduled in Metricool")
    print(f"post {a.id} marked scheduled")


def cmd_persist(cfg, a):
    print("pushed" if pipeline.persist(cfg, a.message) else "push failed")


def cmd_report(cfg, a):
    from .analytics import weekly_report
    out = weekly_report(cfg, DB())
    if out:
        print(pathlib.Path(out).read_text(encoding="utf-8"))
        pipeline.persist(cfg, "Weekly report insights")
    else:
        print("No metrics yet: write Metricool analytics rows to data/metrics.json (see analytics.py) once videos are live.")


def cmd_bank_prompt(cfg, a):
    print(content.bank_prompt(cfg, a.count))


def cmd_bank_import(cfg, a):
    items = content.parse_json(pathlib.Path(a.file).read_text(encoding="utf-8"))
    items = items if isinstance(items, list) else [items]
    good, db = [], DB()
    for i in items:
        p = content.validate(cfg, i)
        if p:
            print(f"REJECTED '{i.get('topic', '?')}': {p}")
        elif db.is_duplicate_topic(i["topic"]) or i["topic"] in [g["topic"] for g in good]:
            print(f"SKIPPED duplicate '{i['topic']}'")
        else:
            good.append(i)
    if good:
        out = config.BANK / f"bank_{dt.datetime.now():%Y%m%d_%H%M%S}.json"
        out.write_text(json.dumps(good, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"imported {len(good)} valid item(s) -> {out}")
    else:
        print("nothing valid to import")


def cmd_test_render(cfg, a):
    from .render import render_video
    from .thumbnail import make_thumbnail
    if a.silent:
        cfg["tts"]["backend"] = "silent"
    item = next((i for i in content._bank_items() if not content.validate(cfg, i)), None)
    if not item:
        sys.exit("No valid item in content_bank/ to render.")
    out = config.DATA / "test_render"
    r = render_video(cfg, item, out)
    make_thumbnail(cfg, item, out / "thumb.jpg")
    print(f"Video: {r['path']} ({r['seconds']:.1f}s, tts={r['tts']})\nThumbnail: {out / 'thumb.jpg'}")


def _check_outputs(cfg, rows):
    """Fail loudly unless every rendered video is 9:16, within length limits, and has audible speech."""
    from .tts import ffprobe_duration
    if not rows:
        print("CHECK FAILED: nothing was built")
        return 1
    bad = 0
    for r in rows:
        v = pathlib.Path(r["video_path"])
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(v)],
                               capture_output=True, text=True).stdout.strip()
        dur = ffprobe_duration(v)
        vol = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(v), "-af", "volumedetect", "-vn", "-f", "null", "-"], capture_output=True, text=True).stderr
        mean = next((float(l.split("mean_volume:")[1].split()[0]) for l in vol.splitlines() if "mean_volume:" in l), -99.0)
        ok = probe == "1080,1920" and cfg["video"]["min_seconds"] <= dur <= cfg["video"]["max_seconds"] and mean > -30
        print(f"CHECK {'OK ' if ok else 'FAIL'} {v.parent.name}: {probe} {dur:.1f}s mean_volume={mean} dB")
        bad += not ok
    return 1 if bad else 0


def cmd_dry_run(cfg, a):
    """Full build against a throwaway state + scratch dir: nothing is staged, pushed or scheduled."""
    import tempfile
    from . import state as st
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="yt_dry_"))
    st.STATE = pipeline.STATE = tmp
    pipeline.DATA = tmp
    if a.silent:
        cfg["tts"]["backend"] = "silent"
    cfg["pipeline"]["buffer_slots"] = a.slots
    db = pipeline.run(cfg, stage=False)
    rows = db.all()
    for r in rows:
        print(r["slot_utc"], r["status"], r["title"], r["video_path"])
    if getattr(a, "check", False):
        return _check_outputs(cfg, rows)


def main(argv=None):
    p = argparse.ArgumentParser(prog="yt_auto", description="XyloMining Shorts pipeline (GitHub media + Metricool scheduling)")
    p.add_argument("--config")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("setup", cmd_setup), ("doctor", cmd_doctor), ("status", cmd_status), ("resume", cmd_resume),
                     ("queue", cmd_queue), ("report", cmd_report)):
        sub.add_parser(name).set_defaults(fn=fn)
    r = sub.add_parser("run"); r.add_argument("--no-stage", action="store_true"); r.set_defaults(fn=cmd_run)
    x = sub.add_parser("approve"); x.add_argument("target", help="post id or 'all'"); x.set_defaults(fn=cmd_approve)
    x = sub.add_parser("reject"); x.add_argument("id", type=int); x.set_defaults(fn=cmd_reject)
    sub.add_parser("pause").set_defaults(fn=cmd_pause)
    x = sub.add_parser("mark-scheduled"); x.add_argument("id", type=int); x.add_argument("--metricool-id", required=True)
    x.add_argument("--uuid", required=True); x.add_argument("--url", default=""); x.set_defaults(fn=cmd_mark_scheduled)
    x = sub.add_parser("persist"); x.add_argument("--message", default="Update pipeline state"); x.set_defaults(fn=cmd_persist)
    x = sub.add_parser("bank-prompt"); x.add_argument("count", type=int, nargs="?", default=30); x.set_defaults(fn=cmd_bank_prompt)
    x = sub.add_parser("bank-import"); x.add_argument("file"); x.set_defaults(fn=cmd_bank_import)
    x = sub.add_parser("test-render"); x.add_argument("--silent", action="store_true"); x.set_defaults(fn=cmd_test_render)
    x = sub.add_parser("dry-run"); x.add_argument("--silent", action="store_true"); x.add_argument("--slots", type=int, default=3); x.add_argument("--check", action="store_true"); x.set_defaults(fn=cmd_dry_run)
    args = p.parse_args(argv)
    cfg = config.load(args.config)
    try:
        return args.fn(cfg, args) or 0
    except Exception as e:  # noqa: BLE001
        get_logger().exception("fatal")
        notify("Shorts pipeline crashed", f"{type(e).__name__}: {e}")
        return 1
