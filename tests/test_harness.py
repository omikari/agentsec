import json
import unittest
from pathlib import Path
from agentsec.core import ALLOWED_ACTIONS, load_scenario, run_matrix, run_scenario

ROOT = Path(__file__).resolve().parents[1]


class BaselineProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = load_scenario(ROOT / 'scenarios/01_soc_benign.json')
        cls.attacked = load_scenario(ROOT / 'scenarios/02_soc_injected.json')

    def test_undefeated_mock_attack_executes_only_synthetic_effect(self):
        result = run_scenario(self.attacked, 'off')
        self.assertTrue(result['metrics']['attack_success'])
        self.assertEqual(result['metrics']['unauthorized_executions'], 1)
        self.assertTrue(result['synthetic_only'])

    def test_action_gate_blocks_attack(self):
        result = run_scenario(self.attacked, 'gate')
        self.assertFalse(result['metrics']['attack_success'])
        self.assertEqual(result['metrics']['unauthorized_executions'], 0)
        self.assertEqual(result['metrics']['unauthorized_attempts'], 1)

    def test_defense_preserves_legitimate_task(self):
        for defense in ('off', 'gate'):
            with self.subTest(defense=defense):
                result = run_scenario(self.clean, defense)
                self.assertTrue(result['metrics']['legitimate_task_complete'])
                self.assertEqual(result['metrics']['false_blocks'], 0)

    def test_provenance_and_policy_decision_logged(self):
        result = run_scenario(self.attacked, 'gate')
        unauthorized = [e for e in result['trace'] if not e['authorized']]
        self.assertEqual(len(unauthorized), 1)
        self.assertEqual(unauthorized[0]['provenance'], 'untrusted:alert.body')
        self.assertEqual(unauthorized[0]['decision'], 'block')

    def test_paired_runs_propose_same_actions(self):
        off = run_scenario(self.attacked, 'off')
        gate = run_scenario(self.attacked, 'gate')
        self.assertEqual([e['proposed_tool'] for e in off['trace']],
                         [e['proposed_tool'] for e in gate['trace']])
        self.assertNotEqual(off['run_id'], gate['run_id'])

    def test_matrix_has_four_runs(self):
        results = run_matrix(ROOT / 'scenarios')
        self.assertEqual(len(results), 4)
        self.assertEqual(len({r['run_id'] for r in results}), 4)

    def test_unknown_defense_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario(self.clean, 'magic')


if __name__ == '__main__':
    unittest.main()
