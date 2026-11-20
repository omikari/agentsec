import json
import unittest
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1] / "scenarios" / "demo"


def load(name):
    return json.loads((DEMO / name).read_text())


class TestDemoScenarios(unittest.TestCase):
    def test_only_the_note_is_different(self):
        benign = load("benign.json")

        for name in [
            "injected.json",
            "injected_v2.json",
            "injected_v3.json",
            "injected_v4.json",
            "injected_v5.json",
        ]:
            other = load(name)
            self.assertEqual(benign["task"], other["task"])
            self.assertEqual(benign["evidence"], other["evidence"])

    def test_attack_only_in_injected(self):
        self.assertNotIn(
            "export_alert_archive",
            load("benign.json")["untrusted_annotation"],
        )

        for name in [
            "injected.json",
            "injected_v2.json",
            "injected_v3.json",
            "injected_v4.json",
            "injected_v5.json",
        ]:
            self.assertIn(
                "export_alert_archive",
                load(name)["untrusted_annotation"],
            )

    def test_answer_key_not_in_scenarios(self):
        for name in [
            "benign.json",
            "injected.json",
            "injected_v2.json",
            "injected_v3.json",
            "injected_v4.json",
            "injected_v5.json",
        ]:
            self.assertNotIn("expected_answer", load(name))


if __name__ == "__main__":
    unittest.main()
