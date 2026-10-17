"""Programmatic 1080x1920 Short renderer: animated background + block-chain motif, headline, big stat,
karaoke captions, progress bar. Frames are drawn with Pillow and piped straight into FFmpeg."""
import math
import pathlib
import subprocess

from PIL import Image, ImageDraw, ImageOps

from .fonts import fit, font, wrap
from .tts import ffprobe_duration, synthesize
from .util import get_logger

BG_TOP, BG_BOT = (14, 18, 34), (4, 6, 14)


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def make_bg(w, h):
    g = Image.linear_gradient("L").resize((w, h))
    return ImageOps.colorize(g, BG_TOP, BG_BOT).convert("RGBA")


def draw_chain(d, w, y, t, accent, seed):
    """Horizontally drifting chain of linked blocks, each with a short pseudo-hash."""
    bw, gap, bh = 230, 70, 170
    step = bw + gap
    off = (t * 90) % step
    f = font(30)
    for k in range(-1, w // step + 3):
        x = int(k * step - off)
        n = int((k + int(t * 90 // step)) + seed)
        h = format((n * 2654435761) & 0xFFFFFFFF, "08x")
        d.line([(x - gap, y + bh // 2), (x, y + bh // 2)], fill=accent + (160,), width=6)
        d.rounded_rectangle([x, y, x + bw, y + bh], 26, outline=accent + (255,), width=5, fill=(255, 255, 255, 14))
        d.text((x + bw // 2, y + 55), "BLOCK", font=f, fill=accent + (255,), anchor="mm")
        d.text((x + bw // 2, y + 110), h[:6] + "…", font=f, fill=(210, 215, 230, 230), anchor="mm")


def draw_dots(d, w, h, t):
    for i in range(46):
        x = (i * 197) % w
        y = (i * 389 + t * (20 + (i % 5) * 9)) % h
        r = 2 + i % 3
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 30 + (i % 4) * 12))


def word_groups(narr, speech, n=4):
    """Split narration into caption groups of ~n words with estimated per-word timings."""
    words = narr.split()
    weights = [max(2, len(w)) for w in words]
    total = sum(weights)
    t, timed = 0.0, []
    for w, wt in zip(words, weights):
        d = speech * wt / total
        timed.append((w, t, t + d))
        t += d
    return [timed[i:i + n] for i in range(0, len(timed), n)]


def draw_caption(d, w, y, groups, lt, accent, cfg_font):
    cur = None
    for g in groups:
        if g[0][1] - 0.05 <= lt:
            cur = g
    if not cur:
        return
    size = 72
    while True:
        f = font(size, cfg_font)
        sp = f.getlength(" ")
        total = sum(f.getlength(x[0]) for x in cur) + sp * (len(cur) - 1)
        if total <= w - 150 or size <= 40:
            break
        size -= 4
    x = (w - total) / 2
    d.rounded_rectangle([x - 36, y - 20, x + total + 36, y + 110], 30, fill=(0, 0, 0, 170))
    for word, a, b in cur:
        active = a <= lt < b
        d.text((x, y), word, font=f, fill=accent + (255,) if active else (255, 255, 255, 255))
        x += f.getlength(word) + sp


def render_video(cfg, item, outdir: pathlib.Path, no_audio_fail=False):
    log = get_logger()
    v = cfg["video"]
    W, H, FPS = v["width"], v["height"], v["render_fps"]
    accent = hex_rgb(v["accent"])
    ff = v.get("font_path", "")
    outdir.mkdir(parents=True, exist_ok=True)

    spec = [{"text": item["hook"], "narration": item["hook"], "hook": True}, *item["scenes"],
            {"text": cfg.get("cta", {}).get("label", "LINK IN DESCRIPTION"), "narration": item["cta"], "cta": True}]
    wav, timing, tts_used = synthesize(cfg, [s["narration"] for s in spec], outdir / "audio")
    total = timing[-1]["end"] + v["tail_seconds"]
    if not v["min_seconds"] <= total <= v["max_seconds"]:
        raise RuntimeError(f"video length {total:.1f}s outside {v['min_seconds']}-{v['max_seconds']}s")

    bg = make_bg(W, H)
    groups = [word_groups(s["narration"], tm["speech"]) for s, tm in zip(spec, timing)]
    out = outdir / "video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav)]
    music = v.get("background_music")
    if music and pathlib.Path(music).exists():
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[2:a]volume={v['music_volume']}[m];[1:a]apad[a];[a][m]amix=inputs=2:duration=first[aout]", "-map", "0:v", "-map", "[aout]"]
    else:
        cmd += ["-af", "apad", "-map", "0:v", "-map", "1:a"]
    cmd += ["-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    nframes = int(total * FPS)
    tag = font(40, ff)
    try:
        for n in range(nframes):
            t = n / FPS
            idx = next((i for i, tm in enumerate(timing) if t < tm["end"]), len(timing) - 1)
            tm, s = timing[idx], spec[idx]
            lt = t - tm["start"]
            img = bg.copy()
            d = ImageDraw.Draw(img, "RGBA")
            draw_dots(d, W, H, t)
            # progress bar (top)
            d.rectangle([0, 0, int(W * t / total), 12], fill=accent + (255,))
            d.text((60, 90), v.get("brand_tag", cfg["brand"]).upper(), font=tag, fill=accent + (255,))

            # headline: slides up + fades in
            a = ease(lt / 0.45)
            hy = 340 + int((1 - a) * 60)
            txt = s["text"] if s.get("hook") else s["text"].upper()
            hf, lines, size = fit(txt, W - 160, 470, 118 if s.get("hook") else 104, 56, ff)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            for li, line in enumerate(lines):
                ld.text((W // 2, hy + li * int(size * 1.12)), line, font=hf, fill=(255, 255, 255, int(255 * a)), anchor="mt")
            img = Image.alpha_composite(img, layer)
            d = ImageDraw.Draw(img, "RGBA")

            # visual: big stat (pulse in) or block chain
            if s.get("stat"):
                sa = ease((lt - 0.2) / 0.5)
                sf = fit(str(s["stat"]), W - 140, 300, int(150 + 40 * sa), 60, ff, max_lines=1)[0]
                d.text((W // 2, 1000), str(s["stat"]), font=sf, fill=accent + (int(255 * sa),), anchor="mm")
            else:
                draw_chain(d, W, 880, t, accent, idx * 7)
            if s.get("cta"):
                pulse = 0.5 + 0.5 * math.sin(t * 5)
                d.rounded_rectangle([W // 2 - 330, 1130, W // 2 + 330, 1260], 50, fill=accent + (int(150 + 100 * pulse),))
                lab = cfg.get("cta", {}).get("label", "LINK IN DESCRIPTION")
                d.text((W // 2, 1195), lab, font=fit(lab, 600, 110, 54, 30, ff, max_lines=1)[0], fill=(10, 10, 20, 255), anchor="mm")

            draw_caption(d, W, 1390, groups[idx], lt, accent, ff)
            proc.stdin.write(img.convert("RGB").tobytes())
        proc.stdin.close()
        err = proc.stderr.read().decode()
        if proc.wait() != 0:
            raise RuntimeError(f"ffmpeg failed: {err[-400:]}")
    except BrokenPipeError:
        raise RuntimeError(f"ffmpeg died: {proc.stderr.read().decode()[-400:]}")
    dur = ffprobe_duration(out)
    log.info("rendered %s (%.1fs, tts=%s)", out, dur, tts_used)
    return {"path": out, "seconds": dur, "tts": tts_used}
