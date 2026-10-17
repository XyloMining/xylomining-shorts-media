"""SQLite state + content log. One row per scheduled slot; the unique constraints are the duplicate guard."""
import datetime as dt
import difflib
import hashlib
import re
import sqlite3

from .config import STATE

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slot_utc TEXT UNIQUE NOT NULL,
  theme TEXT, topic TEXT, topic_hash TEXT UNIQUE,
  status TEXT NOT NULL,
  title TEXT, description TEXT, tags TEXT,
  folder TEXT, video_path TEXT, thumb_path TEXT,
  video_id TEXT, url TEXT,
  video_url TEXT, thumb_url TEXT, metricool_id TEXT, metricool_uuid TEXT, planner_url TEXT,
  tt_metricool_id TEXT, tt_metricool_uuid TEXT, tt_planner_url TEXT,
  attempts INTEGER DEFAULT 0, error TEXT,
  approved_by TEXT,
  created_at TEXT, updated_at TEXT
);
"""
# status: pending_approval -> approved -> staged (media pushed to GitHub) -> scheduled (in Metricool) -> published
#         (also: failed, rejected)


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def topic_hash(topic: str) -> str:
    return hashlib.sha1(norm(topic).encode()).hexdigest()


class DB:
    def __init__(self, path=None):
        STATE.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(path or STATE / "shorts.db"))
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        have = {r[1] for r in self.con.execute("PRAGMA table_info(posts)")}
        for col in ("video_url", "thumb_url", "metricool_id", "metricool_uuid", "planner_url",
                    "tt_metricool_id", "tt_metricool_uuid", "tt_planner_url"):   # migrate DBs created before these existed
            if col not in have:
                self.con.execute(f"ALTER TABLE posts ADD COLUMN {col} TEXT")
        self.con.commit()

    def insert(self, **f):
        f.setdefault("created_at", now_iso())
        f["updated_at"] = now_iso()
        cols = ",".join(f)
        q = ",".join("?" * len(f))
        cur = self.con.execute(f"INSERT INTO posts({cols}) VALUES({q})", list(f.values()))
        self.con.commit()
        return cur.lastrowid

    def update(self, pid, **f):
        f["updated_at"] = now_iso()
        sets = ",".join(f"{k}=?" for k in f)
        self.con.execute(f"UPDATE posts SET {sets} WHERE id=?", [*f.values(), pid])
        self.con.commit()

    def get(self, pid):
        return self.con.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone()

    def by_slot(self, slot_utc):
        return self.con.execute("SELECT * FROM posts WHERE slot_utc=?", (slot_utc,)).fetchone()

    def by_status(self, *statuses):
        q = ",".join("?" * len(statuses))
        return self.con.execute(f"SELECT * FROM posts WHERE status IN ({q}) ORDER BY slot_utc", statuses).fetchall()

    def all(self):
        return self.con.execute("SELECT * FROM posts ORDER BY slot_utc").fetchall()

    def manual_approvals(self) -> int:
        return self.con.execute("SELECT COUNT(*) FROM posts WHERE approved_by='manual'").fetchone()[0]

    def past_topics(self):
        return [r["topic"] for r in self.con.execute("SELECT topic FROM posts WHERE topic IS NOT NULL")]

    def is_duplicate_topic(self, topic: str, threshold=0.82):
        h = topic_hash(topic)
        if self.con.execute("SELECT 1 FROM posts WHERE topic_hash=?", (h,)).fetchone():
            return True
        n = norm(topic)
        return any(difflib.SequenceMatcher(None, n, norm(t)).ratio() >= threshold for t in self.past_topics())
