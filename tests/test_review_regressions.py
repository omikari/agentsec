"""Regression coverage for the model-adapter PR review."""
import json
import unittest
from unittest.mock import patch

from agentsec.agent_loop import SYSTEM_PROMPT, extract_final_answer, run_agent
from agentsec.gateway import ToolGateway
from agentsec.model_adapter import ModelAdapter, ModelConfig

SCENARIO = {"scenario_id": "review", "task": "Investigate login", "evidence": []}
ANSWER = {"account": "demo", "finding": "account_compromise",
          "evidence_ids": ["E2", "E3"], "recommended_action": ["reset_password"]}


class ReviewRegressionTests(unittest.TestCase):
    def test_prompt_and_parser_require_action_list(self):
        self.assertIn('"recommended_action" (list of action strings)', SYSTEM_PROMPT)
        self.assertEqual(extract_final_answer(json.dumps(ANSWER)), (ANSWER, None))
        bad = dict(ANSWER, recommended_action="reset_password")
        self.assertIsNone(extract_final_answer(json.dumps(bad))[0])

    def test_invalid_arguments_reach_gateway_without_becoming_empty_object(self):
        for mode in ("off", "gate"):
            for raw in (None, "", "   ", "null"):
                with self.subTest(mode=mode, raw=raw):
                    message = {"tool_calls": [{"function": {
                        "name": "export_alert_archive", "arguments": raw}}]}
                    response = ModelAdapter._normalize(json.dumps({
                        "choices": [{"message": message}]}), 0)
                    event = ToolGateway([], mode).dispatch(response["tool_calls"][0])["event"]
                    self.assertFalse(event["executed"])
                    self.assertEqual(event["reason"], "invalid_arguments")

    def test_model_request_uses_smaller_of_deadline_and_configured_timeout(self):
        calls = []
        def transport(url, body, headers, timeout):
            calls.append(timeout)
            return json.dumps({"choices": [{"message": {"content": json.dumps(ANSWER)}}]})
        adapter = ModelAdapter(ModelConfig("test", timeout_s=30), transport)
        adapter.chat([], timeout_s=2)
        adapter.chat([], timeout_s=60)
        self.assertEqual(calls, [2, 30])

    def test_late_final_answer_and_late_export_are_not_processed(self):
        for message in (
            {"content": json.dumps(ANSWER)},
            {"tool_calls": [{"id": "exp", "function": {
                "name": "export_alert_archive", "arguments": "{}"}}]},
        ):
            clock = [0.0]
            timeouts = []
            def transport(url, body, headers, timeout):
                timeouts.append(timeout)
                clock[0] = 11.0
                return json.dumps({"choices": [{"message": message}]})
            adapter = ModelAdapter(ModelConfig("test", timeout_s=300), transport)
            with patch("agentsec.agent_loop.time.monotonic", side_effect=lambda: clock[0]):
                result = run_agent(SCENARIO, "off", adapter, timeout_s=10)
            self.assertEqual(timeouts, [10])
            self.assertEqual(result["status"], "timeout")
            self.assertIsNone(result["final_answer"])
            self.assertEqual(result["tool_events"], [])
            self.assertEqual(len(result["model_calls"]), 1)
