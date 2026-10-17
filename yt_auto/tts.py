"""Narration. One audio file per scene so scene timings are exact.

backend auto: kokoro (offline neural, free) -> edge-tts (unofficial, needs Microsoft access)
           -> pyttsx3 (offline, Windows SAPI) -> espeak-ng -> silent timing track.
Captions are always burned in, so a silent fallback still gives a watchable Short.
"""
import asyncio
import pathlib
import shutil
import subprocess

from .config import ROOT
from .util import get_logger, retry

PAD = 0.30  # default pause after each scene (config tts.pad_seconds overrides)


def ffprobe_duration(path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _edge(cfg, text, out):
    import edge_tts

    t = cfg["tts"]

    async def go():
        await edge_tts.Communicate(text, t["voice"], rate=t.get("rate", "+0%")).save(str(out))

    retry(lambda: asyncio.run(go()), tries=3, base=2, what="edge-tts")
    if not pathlib.Path(out).exists() or pathlib.Path(out).stat().st_size < 1000:
        raise RuntimeError("edge-tts produced no audio")


_KOKORO = None


def _kokoro(cfg, text, out):
    """Offline open-source neural TTS (Kokoro-82M via kokoro-onnx). Model fetched by `python -m yt_auto setup`."""
    global _KOKORO
    import soundfile as sf
    from kokoro_onnx import Kokoro

    t = cfg["tts"]
    d = pathlib.Path(t.get("kokoro_model_dir", "models"))
    d = d if d.is_absolute() else ROOT / d
    model, voices = d / "kokoro-v1.0.onnx", d / "voices-v1.0.bin"
    if not model.exists() or not voices.exists():
        raise RuntimeError("Kokoro model files missing - run: python -m yt_auto setup")
    if _KOKORO is None:
        _KOKORO = Kokoro(str(model), str(voices))
    samples, sr = _KOKORO.create(text, voice=t.get("kokoro_voice", "bm_george"), speed=float(t.get("kokoro_speed", 1.0)),
                                 lang=t.get("kokoro_lang", "en-gb"))
    sf.write(str(out), samples, sr, format="WAV")


def _pyttsx3(cfg, text, out):
    import pyttsx3

    e = pyttsx3.init()
    e.save_to_file(text, str(out))
    e.runAndWait()
    if not pathlib.Path(out).exists():
        raise RuntimeError("pyttsx3 produced no audio")


def _espeak(cfg, text, out):
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        raise RuntimeError("espeak not installed")
    subprocess.run([exe, "-w", str(out), text], check=True)


def _silent(cfg, text, out):
    secs = max(1.5, len(text.split()) / cfg["tts"]["words_per_second_fallback"])
    _ff("-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", "-f", "wav", str(out))


def synthesize(cfg, narrations, workdir: pathlib.Path):
    """Returns (wav_path, scenes) where scenes = [{start, end, speech}] in seconds."""
    log = get_logger()
    pad = float(cfg["tts"].get("pad_seconds", PAD))
    workdir.mkdir(parents=True, exist_ok=True)
    pref = cfg["tts"]["backend"]
    chain = {"auto": [("kokoro", _kokoro), ("edge", _edge), ("pyttsx3", _pyttsx3), ("espeak", _espeak), ("silent", _silent)],
             "kokoro": [("kokoro", _kokoro)], "edge": [("edge", _edge)], "pyttsx3": [("pyttsx3", _pyttsx3)], "espeak": [("espeak", _espeak)],
             "silent": [("silent", _silent)]}[pref]
    used = None
    wavs, scenes, t = [], [], 0.0
    for i, text in enumerate(narrations):
        raw = workdir / f"raw_{i}.audio"
        ok = False
        for name, fn in (chain if used is None else [c for c in chain if c[0] == used]):
            try:
                fn(cfg, text, raw)
                used, ok = name, True
                break
            except Exception as e:  # noqa: BLE001
                log.warning("tts backend %s failed: %s", name, str(e)[:200])
        if not ok:
            raise RuntimeError("no TTS backend worked")
        speech = ffprobe_duration(raw)
        wav = workdir / f"scene_{i}.wav"
        _ff("-i", str(raw), "-ar", "44100", "-ac", "1", "-af", f"apad=pad_dur={pad}", str(wav))
        wavs.append(wav)
        scenes.append({"start": t, "end": t + speech + pad, "speech": speech})
        t += speech + pad
    lst = workdir / "list.txt"
    lst.write_text("".join(f"file '{w.resolve().as_posix()}'\n" for w in wavs))
    out = workdir / "narration.wav"
    _ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out))
    master = cfg["tts"].get("master", "")
    if master and used != "silent":
        mastered = workdir / "narration_master.wav"
        _ff("-i", str(out), "-af", master, "-ar", "44100", str(mastered))
        out = mastered
    log.info("narration via %s, %.1fs", used, t)
    return out, scenes, used
