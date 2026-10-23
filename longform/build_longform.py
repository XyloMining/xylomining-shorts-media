"""Long-form (16:9, 1920x1080) explainer builder. Reuses the Shorts narration engine, fonts and look.

    python -m longform.build_longform longform/how_bitcoin_mining_works.json

Writes longform/out/<slug>/{video.mp4, thumbnail.jpg, metadata.json, description.txt}. Nothing is uploaded or scheduled.
"""
import copy
import json
import math
import pathlib
import subprocess
import sys

from PIL import Image, ImageDraw

from yt_auto import config
from yt_auto.fonts import fit, font
from yt_auto.render import draw_caption, draw_chain, draw_dots, ease, hex_rgb, make_bg, word_groups
from yt_auto.tts import ffprobe_duration, synthesize
from yt_auto.util import get_logger

W, H = 1920, 1080
MIN_S, MAX_S = 240, 480  # 4-8 minutes


def mmss(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def flatten(script):
    scenes = []
    for ci, ch in enumerate(script["chapters"]):
        for k, sc in enumerate(ch["scenes"]):
            scenes.append({**sc, "chapter": ci, "first_in_chapter": k == 0, "chapter_name": ch["name"]})
    return scenes


def draw_arrow(d, x, y0, y1, col):
    d.line([(x, y0), (x, y1 - 14)], fill=col, width=6)
    d.polygon([(x - 14, y1 - 18), (x + 14, y1 - 18), (x, y1)], fill=col)


def draw_visual(d, img, vis, lt, dur, accent, ff, t):
    """Right-hand panel, x 1000..1810, y 190..820."""
    X0, X1, Y0, Y1 = 1000, 1810, 190, 820
    cx, cy = (X0 + X1) // 2, (Y0 + Y1) // 2
    typ = vis.get("type", "none")
    if typ == "stat":
        a = ease((lt - 0.2) / 0.5)
        f = fit(vis["value"], X1 - X0, 300, int(170 + 40 * a), 60, ff, max_lines=1)[0]
        d.text((cx, cy - 30), vis["value"], font=f, fill=accent + (int(255 * a),), anchor="mm")
        if vis.get("caption"):
            cf = fit(vis["caption"], X1 - X0, 120, 48, 30, ff, max_lines=2)
            for i, line in enumerate(cf[1]):
                d.text((cx, cy + 110 + i * 56), line, font=cf[0], fill=(255, 255, 255, int(220 * a)), anchor="mm")
    elif typ in ("bullets", "flow", "header"):
        items = vis["items"]
        n = len(items)
        slot = max(1.0, (dur - 1.0) / n)
        box_h = 118 if n <= 4 else 100
        gap = 52 if typ in ("flow", "header") else 28
        total_h = n * box_h + (n - 1) * gap
        y = cy - total_h // 2
        focus = vis.get("focus")
        for i, label in enumerate(items):
            a = ease((lt - 0.3 - i * slot * 0.55) / 0.45)
            if a <= 0:
                y += box_h + gap
                continue
            hot = (focus == i) or (typ == "flow" and i == n - 1)
            fill = accent + (int(230 * a),) if hot else (255, 255, 255, int(26 * a))
            d.rounded_rectangle([X0, y, X1, y + box_h], 26, fill=fill, outline=accent + (int(255 * a),), width=4)
            tf = fit(label, X1 - X0 - 70, box_h - 20, 46, 28, ff, max_lines=2)
            col = (10, 10, 20, int(255 * a)) if hot else (255, 255, 255, int(255 * a))
            if typ == "bullets":
                d.ellipse([X0 + 26, y + box_h // 2 - 9, X0 + 44, y + box_h // 2 + 9], fill=(10, 10, 20, 255) if hot else accent + (255,))
                tx = X0 + 66
            else:
                tx = X0 + 35
            for li, line in enumerate(tf[1]):
                d.text((tx, y + box_h // 2 + (li - (len(tf[1]) - 1) / 2) * tf[2] * 1.1), line, font=tf[0], fill=col, anchor="lm")
            if typ in ("flow", "header") and i < n - 1:
                draw_arrow(d, cx, y + box_h + 4, y + box_h + gap - 2, accent + (int(255 * a),)) if typ == "flow" else None
            y += box_h + gap
        if typ == "header" and vis.get("stat"):
            a = ease((lt - 0.6) / 0.5)
            sf = fit(vis["stat"], 500, 120, 90, 40, ff, max_lines=1)[0]
            d.text((cx, Y1 + 20), vis["stat"] + " total", font=sf, fill=accent + (int(255 * a),), anchor="mm")
    elif typ == "chain":
        draw_chain(d, W, 470, t, accent, 5)


def render(cfg, script, outdir: pathlib.Path):
    log = get_logger()
    v = cfg["video"]
    accent = hex_rgb(v["accent"])
    ff = v.get("font_path", "")
    outdir.mkdir(parents=True, exist_ok=True)
    scenes = flatten(script)

    lcfg = copy.deepcopy(cfg)
    lcfg["tts"]["clause_sync"] = True       # measured timing so captions match the voice
    lcfg["tts"]["pad_seconds"] = 0.55       # slightly longer breathing room between scenes
    wav, timing, used = synthesize(lcfg, [s["narration"] for s in scenes], outdir / "audio")
    total = timing[-1]["end"] + 1.2
    if not MIN_S <= total <= MAX_S:
        raise RuntimeError(f"long-form length {total:.0f}s is outside {MIN_S}-{MAX_S}s")
    log.info("long-form narration %.0fs via %s", total, used)

    groups = [word_groups(s["narration"], tm["speech"], n=6, clauses=tm.get("clauses")) for s, tm in zip(scenes, timing)]
    bg = make_bg(W, H)
    out = outdir / "video.mp4"
    fps = int(v["render_fps"])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-i", str(wav), "-af", "apad", "-map", "0:v", "-map", "1:a", "-t", f"{total:.2f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "25", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    tag, chf, lab = font(38, ff), font(34, ff), font(30, ff)
    nch = len(script["chapters"])
    try:
        for n in range(int(total * fps)):
            t = n / fps
            idx = next((i for i, tm in enumerate(timing) if t < tm["end"]), len(timing) - 1)
            tm, s = timing[idx], scenes[idx]
            lt, dur = t - tm["start"], tm["end"] - tm["start"]
            img = bg.copy()
            d = ImageDraw.Draw(img, "RGBA")
            draw_dots(d, W, H, t)
            d.rectangle([0, 0, int(W * t / total), 10], fill=accent + (255,))
            d.text((90, 52), v.get("brand_tag", cfg["brand"]).upper(), font=tag, fill=accent + (255,))
            d.text((W - 90, 56), f"{s['chapter'] + 1}/{nch}  {s['chapter_name'].upper()}", font=chf, fill=(255, 255, 255, 190), anchor="ra")

            a = ease(lt / 0.5)
            hf, lines, size = fit(s["text"] if idx else script["title"].split(" (")[0], 840, 470, 104, 60, ff, max_lines=4)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            hy = 330 + int((1 - a) * 40) - (len(lines) - 1) * int(size * 0.55)
            for li, line in enumerate(lines):
                ld.text((90, hy + li * int(size * 1.14)), line, font=hf, fill=(255, 255, 255, int(255 * a)), anchor="lt")
            img = Image.alpha_composite(img, layer)
            d = ImageDraw.Draw(img, "RGBA")

            vis = s.get("visual", {"type": "none"})
            vlayer = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # translucent shapes must be drawn on their own layer, then composited
            vd = ImageDraw.Draw(vlayer)
            if vis.get("type", "none") == "none" and idx == 0:
                draw_chain(vd, W, 560, t, accent, 2)
            draw_visual(vd, vlayer, vis, lt, dur, accent, ff, t)
            if s.get("cta"):
                pulse = 0.5 + 0.5 * math.sin(t * 4)
                vd.rounded_rectangle([1000, 420, 1810, 560], 60, fill=accent + (int(150 + 100 * pulse),))
                vd.text((1405, 490), "LINK IN THE DESCRIPTION", font=fit("LINK IN THE DESCRIPTION", 740, 100, 52, 30, ff, max_lines=1)[0], fill=(10, 10, 20, 255), anchor="mm")
            img = Image.alpha_composite(img, vlayer)
            d = ImageDraw.Draw(img, "RGBA")
            if vis.get("footer"):
                d.text((W // 2, 1040), vis["footer"], font=lab, fill=(255, 255, 255, 210), anchor="mm")
            draw_caption(d, W, 880, groups[idx], lt, accent, ff)
            proc.stdin.write(img.convert("RGB").tobytes())
        proc.stdin.close()
        err = proc.stderr.read().decode()
        if proc.wait() != 0:
            raise RuntimeError(f"ffmpeg failed: {err[-400:]}")
    except BrokenPipeError:
        raise RuntimeError(f"ffmpeg died: {proc.stderr.read().decode()[-400:]}")
    log.info("rendered %s (%.0fs)", out, ffprobe_duration(out))
    return out, timing, scenes, total


def thumbnail(cfg, script, out: pathlib.Path):
    TW, TH = 1280, 720
    accent, ff = hex_rgb(cfg["video"]["accent"]), cfg["video"].get("font_path", "")
    img = make_bg(TW, TH)
    cl = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    draw_chain(ImageDraw.Draw(cl), TW, 540, 0.0, accent, 3)
    img = Image.alpha_composite(img, cl)
    d = ImageDraw.Draw(img, "RGBA")
    th = script["thumbnail"]
    f1, l1, sz1 = fit(th["line1"].upper(), TW - 140, 330, 150, 80, ff, max_lines=2)
    y = 100
    for line in l1:
        d.text((70, y), line, font=f1, fill=accent + (255,), anchor="lt")
        y += int(sz1 * 1.1)
    f2, l2, sz2 = fit(th["line2"], TW - 140, 80, 52, 32, ff, max_lines=1)
    y += 10
    for line in l2:
        d.text((70, y), line, font=f2, fill=(255, 255, 255, 255), anchor="lt")
        y += int(sz2 * 1.2)
    d.text((70, 40), cfg["brand"].upper(), font=font(36, ff), fill=(255, 255, 255, 200), anchor="lt")
    rgb = img.convert("RGB")
    for q in (92, 85, 75, 60):
        rgb.save(out, "JPEG", quality=q, optimize=True)
        if out.stat().st_size < 1_900_000:
            break


def metadata(cfg, script, timing, scenes, total, outdir):
    # chapter timestamps: first scene of each chapter; YouTube needs the first at 0:00 and each >= 10 s
    marks = []
    for sc, tm in zip(scenes, timing):
        if sc["first_in_chapter"]:
            marks.append((0 if not marks else tm["start"], sc["chapter_name"]))
    lines = [f"{mmss(t)} {name}" for t, name in marks]
    link = cfg["link"]
    desc = (f"{script['intro']}\n\nChapters:\n" + "\n".join(lines) +
            f"\n\n{cfg['description']['cta_header']}\n{link}\n\n{cfg['description']['disclosure']}\n\nSources:\n" +
            "\n".join(f"- {t}: {u}" for t, u in script["sources"]) + "\n\n#Bitcoin #BitcoinMining #HowItWorks")
    meta = {"title": script["title"], "description": desc, "tags": script["tags"], "category": "SCIENCE_TECHNOLOGY",
            "categoryId": "28", "privacy": "public", "madeForKids": False, "type": "long",
            "durationSeconds": round(total), "chapters": [{"start": mmss(t), "name": n} for t, n in marks]}
    (outdir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (outdir / "description.txt").write_text(desc, encoding="utf-8")
    return meta


def main(path):
    cfg = config.load()
    script = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    outdir = pathlib.Path(__file__).resolve().parent / "out" / script["slug"]
    if len(script["title"]) > 100:
        raise SystemExit("title over 100 characters")
    video, timing, scenes, total = render(cfg, script, outdir)
    thumbnail(cfg, script, outdir / "thumbnail.jpg")
    meta = metadata(cfg, script, timing, scenes, total, outdir)
    print(json.dumps({"video": str(video), "seconds": round(total), "size_mb": round(video.stat().st_size / 1e6, 1),
                      "chapters": meta["chapters"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
