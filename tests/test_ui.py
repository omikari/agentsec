import unittest
from agentsec.ui import execute, scenarios

class UITests(unittest.TestCase):
    def test_mock_compare_uses_both_modes_and_reports_effect(self):
        injected = next(s for s in scenarios("mock") if s["injected"])
        record = execute({"mode": "mock", "scenario": injected["file"], "defense": "compare"})
        off, gate = record["results"]
        self.assertTrue(off["metrics"]["attack_success"])
        self.assertFalse(gate["metrics"]["attack_success"])
        self.assertTrue(all(r["mock"] for r in record["results"]))
        self.assertEqual([r["defense"] for r in record["results"]], ["off", "gate"])

    def test_invalid_scenario_cannot_read_arbitrary_files(self):
        with self.assertRaises(ValueError):
            execute({"mode": "mock", "scenario": "../README.md", "defense": "off"})

    def test_no_silent_fallback_for_invalid_mode_or_defense(self):
        for payload in ({"mode": "unknown", "defense": "off"},
                        {"mode": "mock", "defense": "unknown"}):
            with self.assertRaises(ValueError):
                execute(payload)
