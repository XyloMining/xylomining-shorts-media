"""Pipeline tests with silent narration and git disabled: approval gate, staging, queue format, duplicate guards, pause."""
import datetime as dt, json, pathlib, shutil, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from yt_auto import config, pipeline, state


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        state.STATE = pipeline.STATE = self.tmp / "state"
        pipeline.DATA = self.tmp / "data"
        pipeline.ROOT = self.tmp / "repo"
        for d in (pipeline.STATE, pipeline.DATA, pipeline.ROOT):
            d.mkdir(parents=True)
        self.cfg = config.load()
        self.cfg["tts"]["backend"] = "silent"
        self.cfg["video"]["render_fps"] = 5
        self.cfg["pipeline"]["buffer_slots"] = 3
        self.cfg["media"]["git_push"] = False
        self.alerts = []
        self.p = mock.patch.object(pipeline, "notify", lambda s, b="", level="ERROR": self.alerts.append((level, s)))
        self.p.start()
        self.now = dt.datetime(2026, 10, 16, 9, 0, tzinfo=dt.timezone.utc)  # Fri 20:00 Sydney

    def tearDown(self):
        self.p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def approve_all(self, db):
        for r in db.by_status("pending_approval"):
            db.update(r["id"], status="approved", approved_by="manual")

    def test_gate_stage_queue_mark(self):
        db = pipeline.run(self.cfg, now=self.now)
        self.assertEqual(len(db.by_status("pending_approval")), 3)
        self.assertEqual(db.by_status("staged"), [])                  # gate: nothing staged before approval
        self.assertEqual(pipeline.queue_items(self.cfg, db, self.now), [])
        self.approve_all(db)
        pipeline.run(self.cfg, now=self.now)
        staged = db.by_status("staged")
        self.assertEqual(len(staged), 3)
        for r in staged:
            self.assertTrue(r["video_url"].startswith("https://raw.githubusercontent.com/XyloMining/xylomining-shorts-media/main/videos/"))
            self.assertTrue((pipeline.ROOT / "videos" / pathlib.Path(r["video_url"]).name).exists())
            self.assertTrue((pipeline.ROOT / "log").exists())
        q = pipeline.queue_items(self.cfg, db, self.now)
        self.assertEqual(len(q), 3)
        for it in q:
            info = it["info"]
            self.assertEqual(it["blogId"], "7458399")
            self.assertEqual(info["providers"], [{"network": "youtube"}])
            self.assertEqual(info["youtubeData"]["type"], "short")
            self.assertFalse(info["youtubeData"]["madeForKids"])
            self.assertIn(self.cfg["link"], info["text"])
            self.assertIn("referral link", info["text"])
            self.assertEqual(info["publicationDate"]["timezone"], "Australia/Sydney")
            self.assertRegex(it["date"], r"\+1[01]:00$")                 # Sydney offset, DST-aware
            self.assertNotIn("videoThumbnailUrl", info)                  # off by default
            json.dumps(it)                                               # serialisable
        times = [it["date"] for it in q]
        self.assertEqual(times, sorted(set(times)))
        # mark scheduled; double-scheduling is refused
        pipeline.mark_scheduled(db, q[0]["id"], "123", "uuid-1", "https://app.metricool.com/x")
        with self.assertRaises(ValueError):
            pipeline.mark_scheduled(db, q[0]["id"], "123", "uuid-1", "x")
        self.assertEqual(len(pipeline.queue_items(self.cfg, db, self.now)), 2)

    def test_rerun_is_idempotent(self):
        db = pipeline.run(self.cfg, now=self.now)
        n = len(db.all())
        pipeline.run(self.cfg, now=self.now)
        self.assertEqual(len(db.all()), n)                               # buffer full: nothing new
        self.assertEqual(len({r["topic"] for r in db.all()}), n)         # no duplicate topics

    def test_auto_approve_after_three_manual(self):
        db = pipeline.run(self.cfg, now=self.now)
        self.approve_all(db)
        pipeline.run(self.cfg, now=self.now)
        for r in db.by_status("staged"):
            pipeline.mark_scheduled(db, r["id"], "1", "u", "")
        later = self.now + dt.timedelta(days=4)                          # first three have now passed
        pipeline.run(self.cfg, now=later)
        self.assertTrue(any(r["approved_by"] == "auto" for r in db.all()))

    def test_remaining_pending_auto_approved_after_gate(self):
        db = pipeline.run(self.cfg, now=self.now)
        ids = [r["id"] for r in db.by_status("pending_approval")]
        db.update(ids[0], status="approved", approved_by="manual")
        pipeline.run(self.cfg, now=self.now)
        self.assertEqual(len(db.by_status("pending_approval")), 2)       # only 1 manual approval so far: still gated
        for i in ids[1:]:
            db.update(i, status="approved", approved_by="manual")
        db.update(db.insert(slot_utc="2030-01-01T00:00:00Z", status="pending_approval", topic="zz", topic_hash="zz"), title="x")
        pipeline.run(self.cfg, now=self.now)
        self.assertEqual(db.by_status("pending_approval"), [])           # 3 manual approvals: leftovers auto-approved

    def test_pause_blocks_everything(self):
        pipeline.pause_flag().write_text("x")
        db = pipeline.run(self.cfg, now=self.now)
        self.assertEqual(db.all(), [])

    def test_stale_slot_is_reslotted(self):
        db = pipeline.run(self.cfg, now=self.now)
        first = db.by_status("pending_approval")[0]
        late = self.now + dt.timedelta(days=2)                           # its slot has passed, unapproved
        pipeline.reslot_stale(self.cfg, db, late)
        self.assertGreater(db.get(first["id"])["slot_utc"], first["slot_utc"])

    def test_missing_video_fails_loudly(self):
        db = pipeline.run(self.cfg, now=self.now)
        self.approve_all(db)
        r = db.by_status("approved")[0]
        pathlib.Path(r["video_path"]).unlink()
        pipeline.stage_approved(self.cfg, db)
        self.assertEqual(db.get(r["id"])["status"], "failed")
        self.assertTrue(any("missing" in a[1] for a in self.alerts))


if __name__ == "__main__":
    unittest.main(verbosity=2)
