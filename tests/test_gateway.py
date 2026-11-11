import unittest

from agentsec.gateway import EXPORT, READ, ToolGateway


class GatewayTests(unittest.TestCase):
    def test_same_export_attempt_has_different_effects(self):
        request = {"name": EXPORT, "arguments": {}}
        baseline = ToolGateway([], "off")
        guarded = ToolGateway([], "gate")
        allowed = baseline.dispatch(request)["event"]
        blocked = guarded.dispatch(request)["event"]
        self.assertFalse(allowed["authorized"])
        self.assertFalse(blocked["authorized"])
        self.assertEqual(allowed["decision"], "allow")
        self.assertEqual(blocked["decision"], "block")
        self.assertTrue(allowed["executed"])
        self.assertFalse(blocked["executed"])
        self.assertEqual(allowed["effect"]["type"], "alert_archive_exported")
        self.assertIsNone(blocked["effect"])
        self.assertEqual(baseline.export_count, 1)
        self.assertEqual(guarded.export_count, 0)
        self.assertEqual(ToolGateway([], "off").export_count, 0)

    def test_read_is_available_in_both_modes(self):
        evidence = [{"id": "login-1"}]
        for mode in ("off", "gate"):
            with self.subTest(mode=mode):
                gateway = ToolGateway(evidence, mode)
                response = gateway.dispatch({"name": READ, "arguments": {}})
                self.assertEqual(response["result"]["evidence"], evidence)
                self.assertTrue(response["event"]["authorized"])
                self.assertTrue(response["event"]["executed"])
                self.assertEqual(gateway.export_count, 0)

    def test_baseline_still_rejects_unknown_and_malformed_calls(self):
        gateway = ToolGateway([], "off")
        for request in (
            {"name": "shell", "arguments": {}},
            {"name": EXPORT, "arguments": {"destination": "external"}},
            {"name": EXPORT, "arguments": None},
            {"name": EXPORT, "arguments": []},
            {"name": EXPORT},
        ):
            with self.subTest(request=request):
                event = gateway.dispatch(request)["event"]
                self.assertEqual(event["decision"], "block")
                self.assertFalse(event["executed"])
                self.assertIsNone(event["effect"])
        self.assertEqual(gateway.export_count, 0)
        self.assertEqual(len(gateway.tool_events), 5)
