import datetime as dt, json, os, pathlib, shutil, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from yt_auto import config, content, schedule, state

CFG = config.load()
UTC = dt.timezone.utc


class Schedule(unittest.TestCase):
    def test_times_and_dst(self):
        # AU DST starts Sun 4 Oct 2026 02:00 -> 03:00. Sat 3 Oct 11:00 is AEST(+10), Mon 5 Oct 18:00 is AEDT(+11)
        sat = schedule.slot_for_date(CFG, dt.date(2026, 10, 3))
        mon = schedule.slot_for_date(CFG, dt.date(2026, 10, 5))
        self.assertEqual(schedule.to_utc_iso(sat), "2026-10-03T01:00:00Z")
        self.assertEqual(schedule.to_utc_iso(mon), "2026-10-05T07:00:00Z")
        self.assertEqual((sat.hour, mon.hour), (11, 18))

    def test_weekday_times(self):
        for d in range(7):
            s = schedule.slot_for_date(CFG, dt.date(2026, 11, 2) + dt.timedelta(days=d))
            self.assertEqual(s.hour, 11 if s.weekday() >= 5 else 18)

    def test_upcoming_respects_lead_and_count(self):
        now = dt.datetime(2026, 10, 16, 17, 50, tzinfo=schedule.tz_of(CFG))  # Fri, 10 min before slot
        s = schedule.upcoming_slots(CFG, now, 3, 30)
        self.assertEqual(len(s), 3)
        self.assertEqual(s[0].strftime("%a %H:%M"), "Sat 11:00")  # Fri 18:00 is inside the 30 min lead
        self.assertTrue(all(b > a for a, b in zip(s, s[1:])))

    def test_dst_end(self):
        # DST ends Sun 5 Apr 2026 03:00 -> 02:00; Sun 11:00 must be +10 afterwards
        s = schedule.slot_for_date(CFG, dt.date(2026, 4, 5))
        self.assertEqual(schedule.to_utc_iso(s), "2026-04-05T01:00:00Z")


class Validator(unittest.TestCase):
    def items(self):
        return json.loads(next(config.BANK.glob("claude_week1_2.json")).read_text(encoding="utf-8"))

    def test_bank_all_valid(self):
        for i in self.items():
            self.assertEqual(content.validate(CFG, i), [], i["title"])

    def test_banned_and_money_rejected(self):
        i = self.items()[0]
        i["hook"] = "This is risk-free passive income."
        self.assertTrue(any("banned" in p for p in content.validate(CFG, i)))
        j = self.items()[0]
        j["scenes"][0]["narration"] += " You could earn $500 a day."
        self.assertTrue(any("dollar" in p for p in content.validate(CFG, j)))

    def test_url_in_cta_and_missing_sources(self):
        i = self.items()[0]; i["cta"] = "Go to https://x.com now"
        self.assertTrue(content.validate(CFG, i))
        i = self.items()[0]; i["sources"] = []
        self.assertTrue(content.validate(CFG, i))

    def test_description_has_link_disclosure(self):
        d = content.build_description(CFG, self.items()[0])
        self.assertIn(CFG["link"], d)
        self.assertIn("referral link", d)
        self.assertIn("not guaranteed", d)
        self.assertLessEqual(len(d), 5000)

    def test_parse_json_fenced(self):
        self.assertEqual(content.parse_json('```json\n{"a": 1}\n``` trailing')["a"], 1)

    def test_no_dupe_topics_in_bank(self):
        t = [i["topic"] for i in self.items()]
        self.assertEqual(len(t), len(set(t)))


class Fallback(unittest.TestCase):
    def test_bank_then_gemini(self):
        from unittest import mock
        cfg = config.load(); cfg["llm"]["backend"] = "file+gemini"
        bank = json.loads(next(config.BANK.glob("claude_week1_2.json")).read_text(encoding="utf-8"))
        gen = dict(bank[0], topic="A brand new Gemini-written topic about orange coins", title="Gemini Topic")
        with tempfile.TemporaryDirectory() as d:
            db = state.DB(pathlib.Path(d) / "t.db")
            slot = dt.datetime(2026, 10, 19, 18, 0, tzinfo=schedule.tz_of(cfg))
            with mock.patch.object(content, "_bank_items", lambda: bank):
                self.assertIn(content.generate(cfg, db, slot)["topic"], [b["topic"] for b in bank])   # bank wins while it has items
            with mock.patch.object(content, "_bank_items", lambda: []), \
                 mock.patch.object(content, "_gemini", lambda c, p: "```json\n" + json.dumps(gen) + "\n```"):
                self.assertEqual(content.generate(cfg, db, slot)["title"], "Gemini Topic")             # fallback after bank is empty
            bad = dict(gen, hook="This is risk-free passive income.")
            with mock.patch.object(content, "_bank_items", lambda: []), \
                 mock.patch.object(content, "_gemini", lambda c, p: json.dumps(bad)):
                with self.assertRaises(RuntimeError):                                                   # validator still gates Gemini output
                    content.generate(cfg, db, slot)


class Dupes(unittest.TestCase):
    def test_db_blocks_dupes(self):
        with tempfile.TemporaryDirectory() as d:
            db = state.DB(pathlib.Path(d) / "t.db")
            db.insert(slot_utc="2026-10-17T07:00:00Z", topic="How a block gets mined", topic_hash=state.topic_hash("How a block gets mined"), status="approved")
            self.assertTrue(db.is_duplicate_topic("How a Block Gets Mined!"))
            self.assertTrue(db.is_duplicate_topic("How a block actually gets mined"))
            self.assertFalse(db.is_duplicate_topic("Why halvings exist"))
            with self.assertRaises(Exception):  # same slot twice
                db.insert(slot_utc="2026-10-17T07:00:00Z", topic="x", topic_hash="x", status="approved")


class Analytics(unittest.TestCase):
    def test_report_from_rows(self):
        from yt_auto import analytics
        with tempfile.TemporaryDirectory() as d:
            analytics.STATE = pathlib.Path(d)
            db = state.DB(pathlib.Path(d) / "t.db")
            for n in range(4):
                db.insert(slot_utc=f"2026-10-1{n}T07:00:00Z", topic=f"t{n}", topic_hash=str(n), status="published", title=f"Title {n}", folder=d)
            rows = [{"title": f"Title {n}", "views": 100 * (n + 1), "engagedViews": 80 * (n + 1), "averageViewDuration": 20,
                     "averageViewPercentage": 50 + n * 10, "likes": n, "comments": 0, "subscribersGained": n} for n in range(4)]
            rows.append({"title": "Unrelated video", "views": 9999})  # not ours -> ignored
            out = analytics.weekly_report(CFG, db, today=dt.date(2026, 10, 18), rows=rows)
            txt = out.read_text(encoding="utf-8")
            self.assertIn("Top 3", txt)
            self.assertIn("Not measurable through the API", txt)
            self.assertNotIn("Unrelated", txt)
            self.assertLess(txt.index("Title 3"), txt.index("Title 0"))
            self.assertTrue((pathlib.Path(d) / "insights.json").exists())
            out.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
