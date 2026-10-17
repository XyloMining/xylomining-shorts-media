"""Alerts: always logged to logs/alerts.log; also Discord webhook and/or SMTP email if configured in .env."""
import datetime as dt
import os
import smtplib
from email.message import EmailMessage

import requests

from .config import LOGS
from .util import get_logger


def notify(subject: str, body: str = "", level: str = "ERROR") -> None:
    log = get_logger()
    stamp = dt.datetime.now().isoformat(timespec="seconds")
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / "alerts.log", "a", encoding="utf-8") as f:
        f.write(f"{stamp} [{level}] {subject}\n{body}\n---\n")
    log.warning("ALERT [%s] %s", level, subject)

    hook = os.environ.get("DISCORD_WEBHOOK_URL")
    if hook:
        try:
            requests.post(hook, json={"content": f"**[{level}] {subject}**\n{body}"[:1900]}, timeout=15)
        except Exception as e:  # noqa: BLE001
            log.error("discord notify failed: %s", e)

    host, to = os.environ.get("SMTP_HOST"), os.environ.get("NOTIFY_EMAIL_TO")
    if host and to:
        try:
            msg = EmailMessage()
            msg["Subject"] = f"[Shorts bot] {subject}"
            msg["From"] = os.environ.get("SMTP_USER", to)
            msg["To"] = to
            msg.set_content(body or subject)
            with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=30) as s:
                s.starttls()
                if os.environ.get("SMTP_USER"):
                    s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASS", ""))
                s.send_message(msg)
        except Exception as e:  # noqa: BLE001
            log.error("email notify failed: %s", e)
