import os
import pathlib

import yaml

ROOT = pathlib.Path(os.environ.get("YT_AUTO_HOME", pathlib.Path(__file__).resolve().parent.parent))
DATA = ROOT / "data"          # scratch, git-ignored (renders, locks)
STATE = ROOT / "state"        # committed: shorts.db, PAUSED flag, insights.json
SECRETS = ROOT / "secrets"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports"
BANK = ROOT / "content_bank"
FACTS = ROOT / "facts"

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _load_dotenv(path: pathlib.Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load(path=None) -> dict:
    for d in (DATA, STATE, SECRETS, LOGS, REPORTS):
        d.mkdir(parents=True, exist_ok=True)
    _load_dotenv(ROOT / ".env")
    p = pathlib.Path(path or os.environ.get("YT_AUTO_CONFIG", ROOT / "config.yaml"))
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    missing = [d for d in DAYS if d not in cfg.get("schedule", {})]
    if missing:
        raise ValueError(f"config.yaml schedule is missing days: {missing}")
    for d in DAYS:
        h, m = cfg["schedule"][d]["time"].split(":")
        if not (0 <= int(h) < 24 and 0 <= int(m) < 60):
            raise ValueError(f"bad time for {d}: {cfg['schedule'][d]['time']}")
    if not cfg.get("link", "").startswith("https://"):
        raise ValueError("config.yaml: link must be an https URL")
