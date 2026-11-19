import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentsec import ui
from agentsec.connections import connection_config, test_connection
from agentsec.model_adapter import ModelUnreachable
from test_agent_loop import FakeAdapter, tool_call, final

ROOT = Path(__file__).resolve().parents[1]
ANSWER = json.loads((ROOT / 'scenarios/demo/answer_correct.json').read_text())


class IntegrationTests(unittest.TestCase):
    def test_four_conditions_through_ui_with_scripted_adapter(self):
        for scenario in ('benign.json', 'injected.json'):
            for defense in ('off', 'gate'):
                script = [tool_call('read_login_evidence')]
                if scenario == 'injected.json':
                    script.append(tool_call('export_alert_archive'))
                script.append(final(json.dumps(ANSWER)))
                with patch('agentsec.model_adapter.ModelAdapter', return_value=FakeAdapter(script)):
                    result = ui.execute({'mode': 'real', 'scenario': scenario,
                                         'defense': defense, 'model': 'scripted'})['results'][0]
                self.assertEqual(result['status'], 'completed')
                self.assertTrue(result['scores']['task_passed'])
                self.assertTrue(result['annotation_exposed'])
                self.assertEqual(result['scores']['attack_success'], scenario == 'injected.json' and defense == 'off')
                self.assertEqual(len(result['scenario_hash']), 64)

    def test_variant_roundtrip_preserves_preset_and_evidence(self):
        original = (ROOT / 'scenarios/demo/benign.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder, patch.object(ui, 'VARIANTS', Path(folder)):
            result = ui.save_variant({'scenario': 'benign.json', 'annotation': 'new note'})
            saved = json.loads(ui.scenario_path('real', result['file']).read_text())
            self.assertEqual(saved['untrusted_annotation'], 'new note')
            self.assertEqual(saved['evidence'], json.loads(original)['evidence'])
            self.assertTrue(saved['exploratory'])
            self.assertEqual((ROOT / 'scenarios/demo/benign.json').read_bytes(), original)
            with self.assertRaises(ValueError):
                ui.save_variant({'scenario': '../README.md', 'annotation': ''})

    def test_credentials_are_not_forwarded_to_another_endpoint(self):
        with patch.dict('os.environ', {'AGENTSEC_MODEL_API_KEY': 'secret',
                                     'AGENTSEC_MODEL_BASE_URL': 'http://localhost:11434/v1'}):
            self.assertIsNone(connection_config({'model': 'm', 'base_url': 'http://other.test/v1'}).api_key)
        for url in ('file:///secret', 'http://user:pass@host/v1', 'http://host/v1?key=secret'):
            with self.assertRaises(ValueError):
                connection_config({'model': 'm', 'base_url': url})

    def test_connection_states(self):
        with patch('agentsec.connections.discover_models', return_value={'status': 'reachable', 'models': []}):
            self.assertEqual(test_connection({'model': 'm'})['status'], 'missing_model')
        with patch('agentsec.connections.discover_models', return_value={'status': 'discovery_unavailable'}), \
             patch('agentsec.connections.ModelAdapter') as adapter:
            adapter.return_value.chat.side_effect = ModelUnreachable('offline')
            self.assertEqual(test_connection({'model': 'm'})['status'], 'model_unreachable')
            adapter.return_value.chat.side_effect = None
            adapter.return_value.chat.return_value = tool_call('read_login_evidence')
            self.assertEqual(test_connection({'model': 'm'})['status'], 'tool_compatible')
            adapter.return_value.chat.return_value = final('hello')
            self.assertEqual(test_connection({'model': 'm'})['status'], 'tool_incompatible')
