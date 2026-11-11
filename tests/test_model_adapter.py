"""Offline tests for the real-model adapter. No network; a fake transport
stands in for the HTTP call. The live test runs only with AGENTSEC_LIVE_MODEL=1."""
import io
import json
import os
import socket
import unittest
import urllib.error

from agentsec.gateway import tool_definitions
from agentsec.model_adapter import (
    BadModelResponse, ModelAdapter, ModelConfig, ModelConfigError, ModelTimeout,
    ModelUnreachable, parse_arguments, to_openai_tools,
)


def completion(message, finish_reason="stop", usage=None):
    return json.dumps({"choices": [{"message": message, "finish_reason": finish_reason}],
                       "usage": usage or {"prompt_tokens": 1, "completion_tokens": 1}})


class RecordingTransport:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    def __call__(self, url, body, headers, timeout_s):
        self.calls.append({"url": url, "body": json.loads(body), "headers": headers, "timeout_s": timeout_s})
        if self.error is not None:
            raise self.error
        return self.reply


CONFIG = ModelConfig(model="llama3.1:8b", base_url="http://model.test/v1")


class ConfigTests(unittest.TestCase):
    def test_from_env_reads_settings(self):
        cfg = ModelConfig.from_env(env={
            "AGENTSEC_MODEL": "llama3.1:8b", "AGENTSEC_MODEL_BASE_URL": "http://x/v1/",
            "AGENTSEC_MODEL_TIMEOUT_S": "30", "AGENTSEC_MODEL_SEED": "7",
        })
        self.assertEqual((cfg.model, cfg.base_url, cfg.timeout_s, cfg.seed, cfg.temperature),
                         ("llama3.1:8b", "http://x/v1", 30.0, 7, 0.0))
        self.assertEqual(cfg.max_tokens, 512)
        self.assertIsNone(ModelConfig.from_env(env={"AGENTSEC_MODEL": "m",
                                                    "AGENTSEC_MODEL_MAX_TOKENS": "none"}).max_tokens)

    def test_missing_model_is_config_error(self):
        with self.assertRaises(ModelConfigError):
            ModelConfig.from_env(env={})

    def test_guard_role_uses_own_prefix(self):
        cfg = ModelConfig.from_env(prefix="AGENTSEC_GUARD_MODEL", role="guard",
                                   env={"AGENTSEC_GUARD_MODEL": "qwen3:8b"})
        self.assertEqual((cfg.model, cfg.role), ("qwen3:8b", "guard"))

    def test_describe_never_leaks_api_key(self):
        cfg = ModelConfig(model="m", api_key="sk-secret")
        meta = cfg.describe()
        self.assertNotIn("sk-secret", json.dumps(meta))
        self.assertNotIn("sk-secret", repr(cfg))
        self.assertTrue(meta["api_key_set"])
        self.assertEqual(meta["tool_mode"], "native")


class ConversionTests(unittest.TestCase):
    def test_wraps_gateway_tools(self):
        tools = to_openai_tools(tool_definitions())
        self.assertEqual([t["type"] for t in tools], ["function", "function"])
        self.assertEqual({t["function"]["name"] for t in tools},
                         {"read_login_evidence", "export_alert_archive"})

    def test_parse_arguments(self):
        self.assertEqual(parse_arguments(""), {})
        self.assertEqual(parse_arguments(None), {})
        self.assertEqual(parse_arguments({"a": 1}), {"a": 1})
        self.assertEqual(parse_arguments('{"a": 1}'), {"a": 1})
        self.assertEqual(parse_arguments("{not json"), "{not json")


class ChatTests(unittest.TestCase):
    def test_request_shape_and_tool_call_normalized(self):
        transport = RecordingTransport(completion({
            "role": "assistant", "content": "",
            "tool_calls": [{"id": "call_1", "type": "function",
                            "function": {"name": "read_login_evidence", "arguments": "{}"}}],
        }, finish_reason="tool_calls"))
        out = ModelAdapter(CONFIG, transport).chat([{"role": "user", "content": "hi"}], tool_definitions())
        sent = transport.calls[0]
        self.assertEqual(sent["url"], "http://model.test/v1/chat/completions")
        self.assertEqual((sent["body"]["temperature"], sent["body"]["seed"], sent["body"]["max_tokens"]),
                         (0.0, 0, 512))
        self.assertEqual(len(sent["body"]["tools"]), 2)
        self.assertNotIn("Authorization", sent["headers"])
        self.assertIsNone(out["content"])
        self.assertEqual(out["tool_calls"], [{"id": "call_1", "name": "read_login_evidence", "arguments": {}}])
        self.assertEqual(out["raw_finish_reason"], "tool_calls")

    def test_text_reply(self):
        out = ModelAdapter(CONFIG, RecordingTransport(completion(
            {"role": "assistant", "content": '{"account": "a"}'}))).chat([])
        self.assertEqual(out["content"], '{"account": "a"}')
        self.assertEqual(out["tool_calls"], [])

    def test_unparseable_arguments_pass_through(self):
        out = ModelAdapter(CONFIG, RecordingTransport(completion({"role": "assistant", "tool_calls": [
            {"function": {"name": "export_alert_archive", "arguments": "{oops"}}]}))).chat([])
        self.assertEqual(out["tool_calls"][0]["arguments"], "{oops")
        self.assertTrue(out["tool_calls"][0]["id"].startswith("call_"))

    def test_reasoning_effort_sent_only_when_set(self):
        transport = RecordingTransport(completion({"role": "assistant", "content": "x"}))
        ModelAdapter(CONFIG, transport).chat([])
        self.assertNotIn("reasoning_effort", transport.calls[0]["body"])
        cfg = ModelConfig.from_env(env={"AGENTSEC_MODEL": "qwen3:8b", "AGENTSEC_MODEL_REASONING_EFFORT": "none"})
        ModelAdapter(cfg, transport).chat([])
        self.assertEqual(transport.calls[1]["body"]["reasoning_effort"], "none")
        self.assertEqual(cfg.describe()["reasoning_effort"], "none")

    def test_api_key_sent_as_bearer(self):
        transport = RecordingTransport(completion({"role": "assistant", "content": "x"}))
        ModelAdapter(ModelConfig(model="m", api_key="k"), transport).chat([])
        self.assertEqual(transport.calls[0]["headers"]["Authorization"], "Bearer k")


class ErrorTests(unittest.TestCase):
    def chat_raises(self, error=None, reply=None):
        return ModelAdapter(CONFIG, RecordingTransport(reply=reply, error=error)).chat([])

    def test_connection_refused_is_unreachable(self):
        with self.assertRaises(ModelUnreachable):
            self.chat_raises(error=urllib.error.URLError(ConnectionRefusedError(61, "refused")))

    def test_timeout(self):
        with self.assertRaises(ModelTimeout):
            self.chat_raises(error=socket.timeout("timed out"))
        with self.assertRaises(ModelTimeout):
            self.chat_raises(error=urllib.error.URLError(socket.timeout("timed out")))

    def test_http_error_is_bad_response(self):
        err = urllib.error.HTTPError("u", 404, "nf", {}, io.BytesIO(b'{"error":"model not found"}'))
        with self.assertRaisesRegex(BadModelResponse, "model not found"):
            self.chat_raises(error=err)

    def test_garbage_body_is_bad_response(self):
        with self.assertRaises(BadModelResponse):
            self.chat_raises(reply="<html>not json</html>")
        with self.assertRaises(BadModelResponse):
            self.chat_raises(reply='{"choices": []}')


@unittest.skipUnless(os.environ.get("AGENTSEC_LIVE_MODEL") == "1",
                     "live model test; set AGENTSEC_LIVE_MODEL=1 and AGENTSEC_MODEL to run")
class LiveModelTests(unittest.TestCase):
    def test_live_model_requests_read_tool(self):
        adapter = ModelAdapter.from_env()
        out = adapter.chat([
            {"role": "system", "content": "You are a SOC analyst assistant. Use tools to get case data."},
            {"role": "user", "content": "Review the login alert. Start by reading the login evidence."},
        ], tool_definitions())
        self.assertIn("read_login_evidence", [c["name"] for c in out["tool_calls"]])


if __name__ == "__main__":
    unittest.main()
