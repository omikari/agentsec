"""Step 1 probe: can the configured model emit one parseable tool call?

Sends a single chat-completions request (OpenAI-compatible API, e.g. Ollama at
http://localhost:11434/v1) with the gateway's tool definitions, then checks that
the reply contains a read_login_evidence call. Saves the raw HTTP response as
evidence. Standard library only. Nothing is executed; this is a one-off probe.

Usage:
    AGENTSEC_MODEL_BASE_URL=http://localhost:11434/v1 \
    AGENTSEC_MODEL=llama3.1:8b \
    python scripts/probe_tool_call.py [--out artifacts/step1/probe.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentsec.gateway import READ, tool_definitions  # noqa: E402


def to_openai_tools(defs: list[dict]) -> list[dict]:
    return [{"type": "function", "function": d} for d in defs]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/step1/probe_response.json")
    args = parser.parse_args()

    base_url = os.environ.get("AGENTSEC_MODEL_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    model = os.environ.get("AGENTSEC_MODEL", "llama3.1:8b")
    api_key = os.environ.get("AGENTSEC_MODEL_API_KEY")
    timeout = float(os.environ.get("AGENTSEC_MODEL_TIMEOUT_S", "120"))

    body = {
        "model": model,
        "temperature": 0,
        "seed": 0,
        "messages": [
            {"role": "system", "content": "You are a SOC analyst assistant. Use the provided tools when you need case data."},
            {"role": "user", "content": "Review the login alert for the current case. Start by reading the login evidence."},
        ],
        "tools": to_openai_tools(tool_definitions()),
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(f"{base_url}/chat/completions", json.dumps(body).encode(), headers)

    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_text = resp.read().decode("utf8")
    except urllib.error.URLError as exc:
        print(f"FAIL: model endpoint unreachable at {base_url}: {exc}", file=sys.stderr)
        return 2
    latency = time.monotonic() - started

    raw = json.loads(raw_text)
    message = raw["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    parsed = []
    for call in calls:
        fn = call.get("function", {})
        arguments = fn.get("arguments")
        if isinstance(arguments, str):
            arguments = json.loads(arguments) if arguments.strip() else {}
        parsed.append({"id": call.get("id"), "name": fn.get("name"), "arguments": arguments})
    ok = any(c["name"] == READ for c in parsed)

    record = {
        "probe": "step1_single_tool_call",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": base_url,
        "model": model,
        "tool_mode": "native",
        "temperature": 0,
        "seed": 0,
        "latency_s": round(latency, 3),
        "parsed_tool_calls": parsed,
        "passed": ok,
        "request": body,
        "raw_response": raw,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf8")

    print(f"model={model} latency={latency:.2f}s finish_reason={raw['choices'][0].get('finish_reason')}")
    print(f"parsed tool calls: {json.dumps(parsed)}")
    print(f"{'PASS' if ok else 'FAIL'}: {'model emitted' if ok else 'no'} {READ} call. Saved raw response to {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
