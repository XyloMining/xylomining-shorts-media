"""Slot calculation in Australia/Sydney (or any IANA zone) with correct DST handling."""
import datetime as dt
from zoneinfo import ZoneInfo

from .config import DAYS


def tz_of(cfg) -> ZoneInfo:
    return ZoneInfo(cfg["timezone"])


def slot_for_date(cfg, d: dt.date) -> dt.datetime:
    ent = cfg["schedule"][DAYS[d.weekday()]]
    h, m = (int(x) for x in ent["time"].split(":"))
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=tz_of(cfg))


def theme_for(cfg, slot: dt.datetime) -> str:
    return cfg["schedule"][DAYS[slot.weekday()]]["theme"]


def upcoming_slots(cfg, now: dt.datetime, count: int, min_lead_minutes: int = 30):
    """The next `count` slots that start at least min_lead_minutes after `now`."""
    tz = tz_of(cfg)
    now = now.astimezone(tz)
    earliest = now + dt.timedelta(minutes=min_lead_minutes)
    out, d = [], now.date()
    for _ in range(count + 15):
        if DAYS[d.weekday()] not in cfg["schedule"]:   # days left out of the schedule are skipped
            d += dt.timedelta(days=1)
            continue
        s = slot_for_date(cfg, d)
        if s > earliest:
            out.append(s)
            if len(out) == count:
                break
        d += dt.timedelta(days=1)
    return out


def to_utc_iso(slot: dt.datetime) -> str:
    return slot.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def from_utc_iso(s: str, cfg) -> dt.datetime:
    return dt.datetime.strptime(s[:20], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).astimezone(tz_of(cfg))
