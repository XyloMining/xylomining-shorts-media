import logging
import logging.handlers
import os
import time

from .config import DATA, LOGS

_LOGGER = None


def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER:
        return _LOGGER
    LOGS.mkdir(parents=True, exist_ok=True)
    lg = logging.getLogger("yt_auto")
    lg.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.handlers.RotatingFileHandler(LOGS / "yt_auto.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    lg.addHandler(fh)
    lg.addHandler(sh)
    _LOGGER = lg
    return lg


def retry(fn, tries=4, base=3.0, retriable=lambda e: True, what="operation"):
    """Call fn(); on retriable exceptions wait base*2**i seconds and try again."""
    log = get_logger()
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1 or not retriable(e):
                raise
            wait = base * (2 ** i)
            log.warning("%s failed (%s); retry %d/%d in %.0fs", what, e, i + 1, tries - 1, wait)
            time.sleep(wait)


class Locked(RuntimeError):
    pass


class RunLock:
    """Prevents two overlapping runs (e.g. a slow render and the next scheduled start)."""

    def __init__(self, name="run.lock", stale_seconds=3 * 3600):
        self.path = DATA / name
        self.stale = stale_seconds

    def __enter__(self):
        DATA.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and time.time() - self.path.stat().st_mtime < self.stale:
            raise Locked(f"another run is active ({self.path})")
        self.path.write_text(str(os.getpid()))
        return self

    def __exit__(self, *a):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
