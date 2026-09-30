#!/usr/bin/env python3
"""fetch_icu.py 纯函数单元测试（无需网络）。

运行：
    python3 -m unittest tests.test_fetch_icu -v
    或
    python3 tests/test_fetch_icu.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skill", "scripts"))
import fetch_icu as f


class TestExtractThresholds(unittest.TestCase):
    def test_cycle_sport_settings_identified(self):
        profile = {"athlete": {"name": "Tester", "weight": 80, "maxHR": 209}}
        settings = [{"types": ["Ride", "VirtualRide"], "ftp": 200, "lthr": 189, "max_hr": 209}]
        info = f.extract_thresholds(profile, settings)
        self.assertEqual(info["ftp"], 200)
        self.assertEqual(info["lthr"], 189)
        self.assertEqual(info["name"], "Tester")

    def test_non_cycle_settings_ignored(self):
        profile = {"athlete": {}}
        settings = [
            {"types": ["Run"], "ftp": 999, "lthr": 150},
            {"types": ["Ride"], "ftp": 200, "lthr": 189},
        ]
        info = f.extract_thresholds(profile, settings)
        self.assertEqual(info["ftp"], 200)

    def test_missing_athlete_unwrap(self):
        profile = {"name": "Flat"}
        info = f.extract_thresholds(profile, [])
        self.assertEqual(info["name"], "Flat")


class TestFmtActivities(unittest.TestCase):
    def test_field_mapping(self):
        acts = [{
            "start_date_local": "2026-09-27T19:00:00",
            "name": "Evening 虚拟骑行",
            "type": "VirtualRide",
            "distance": 18100,
            "moving_time": 2760,
            "icu_training_load": 32,
            "icu_weighted_avg_watts": 130,
            "icu_intensity": 65,
            "icu_average_watts": 127,
            "average_heartrate": 135,
        }]
        rows = f.fmt_activities(acts)
        self.assertEqual(rows[0]["date"], "2026-09-27")
        self.assertEqual(rows[0]["distance_km"], 18.1)
        self.assertEqual(rows[0]["minutes"], 46)
        self.assertEqual(rows[0]["if"], 0.65)
        self.assertEqual(rows[0]["load"], 32)

    def test_missing_fields_tolerated(self):
        rows = f.fmt_activities([{"start_date_local": "2026-09-01"}])
        self.assertIsNone(rows[0]["distance_km"])
        self.assertIsNone(rows[0]["if"])


class TestFmtWellness(unittest.TestCase):
    def test_tsb_calc_and_stress(self):
        wl = [{"id": "2026-09-29", "ctl": 26.72, "atl": 47.50,
               "restingHR": 57, "hrv": 45, "sleepSecs": 19800, "stress": 42}]
        w = f.fmt_wellness(wl)
        self.assertAlmostEqual(w["tsb"], -20.8, places=1)
        self.assertEqual(w["stress"], 42)
        self.assertEqual(w["restingHR"], 57)

    def test_empty_input(self):
        self.assertIsNone(f.fmt_wellness([]))

    def test_tsb_none_when_missing(self):
        w = f.fmt_wellness([{"id": "x", "ctl": 10}])
        self.assertIsNone(w["tsb"])


class TestInterpretTsb(unittest.TestCase):
    def test_boundaries(self):
        self.assertIn("恢复", f.interpret_tsb(30))
        self.assertIn("比赛窗口", f.interpret_tsb(15))
        self.assertIn("灰色", f.interpret_tsb(5))
        self.assertIn("最佳训练区", f.interpret_tsb(-10))
        self.assertIn("过度训练", f.interpret_tsb(-30))
        self.assertIn("高风险", f.interpret_tsb(-31))
        self.assertIsNone(f.interpret_tsb(None))


class TestInterpretRamp(unittest.TestCase):
    def test_boundaries(self):
        self.assertIn("维持", f.interpret_ramp(2))
        self.assertIn("保守", f.interpret_ramp(5))
        self.assertIn("积极", f.interpret_ramp(7))
        self.assertIn("风险", f.interpret_ramp(8))
        self.assertIsNone(f.interpret_ramp(None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
