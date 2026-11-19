"""Real-model adapter for an OpenAI-compatible chat completions endpoint.

One adapter covers Ollama (http://localhost:11434/v1) and vLLM, which serve the
same API. Standard library only. It never falls back to the mock: failures
raise a typed ModelError so the caller can record them explicitly.

The adapter is role-neutral. The agent uses the AGENTSEC_MODEL_* variables;
a later guard/verifier role can use its own prefix, e.g.
ModelConfig.from_env(prefix="AGENTSEC_GUARD_MODEL", role="guard").
"""
from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Callable

TOOL_MODE = "native"
DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_TIMEOUT_S = 300.0
DEFAULT_TEMPERATURE = 0.0
DEFAULT_SEED = 0
DEFAULT_MAX_TOKENS = 512


class ModelError(Exception):
    """Base class for real-model failures. Never caught by a mock fallback."""

    kind = "model_error"


class ModelConfigError(ModelError):
    kind = "model_config_error"


class ModelUnreachable(ModelError):
    kind = "model_unreachable"


class ModelTimeout(ModelError):
    kind = "model_timeout"


class BadModelResponse(ModelError):
    kind = "bad_model_response"


@dataclass(frozen=True)
class ModelConfig:
    model: str
    base_url: str = DEFAULT_BASE_URL
    api_key: str | None = field(default=None, repr=False)
    timeout_s: float = DEFAULT_TIMEOUT_S
    temperature: float = DEFAULT_TEMPERATURE
    seed: int | None = DEFAULT_SEED
    max_tokens: int | None = DEFAULT_MAX_TOKENS
    # e.g. "none" to turn off Qwen3-style thinking; None = endpoint default (not sent).
    reasoning_effort: str | None = None
    role: str = "agent"

    @classmethod
    def from_env(cls, prefix: str = "AGENTSEC_MODEL", role: str = "agent",
                 env: dict | None = None) -> "ModelConfig":
        """Read <prefix>_BASE_URL, <prefix> (model name), <prefix>_API_KEY,
        <prefix>_TIMEOUT_S, <prefix>_TEMPERATURE, <prefix>_SEED, <prefix>_MAX_TOKENS and <prefix>_REASONING_EFFORT."""
        env = os.environ if env is None else env
        model = (env.get(prefix) or "").strip()
        if not model:
            raise ModelConfigError(f"Set {prefix} to the model name, e.g. {prefix}=llama3.1:8b")
        try:
            timeout_s = float(env.get(f"{prefix}_TIMEOUT_S", DEFAULT_TIMEOUT_S))
            temperature = float(env.get(f"{prefix}_TEMPERATURE", DEFAULT_TEMPERATURE))
            seed_raw = env.get(f"{prefix}_SEED", str(DEFAULT_SEED)).strip()
            seed = None if seed_raw.lower() in ("", "none") else int(seed_raw)
            max_raw = env.get(f"{prefix}_MAX_TOKENS", str(DEFAULT_MAX_TOKENS)).strip()
            max_tokens = None if max_raw.lower() in ("", "none") else int(max_raw)
        except ValueError as exc:
            raise ModelConfigError(f"Bad numeric setting for {prefix}: {exc}") from exc
        return cls(
            model=model,
            base_url=(env.get(f"{prefix}_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
            api_key=env.get(f"{prefix}_API_KEY") or None,
            timeout_s=timeout_s,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
            reasoning_effort=(env.get(f"{prefix}_REASONING_EFFORT") or "").strip() or None,
            role=role,
        )

    def describe(self) -> dict:
        """Metadata safe to store in a run result. Never includes the API key."""
        return {
            "name": self.model,
            "base_url": self.base_url,
            "role": self.role,
            "tool_mode": TOOL_MODE,
            "temperature": self.temperature,
            "seed": self.seed,
            "max_tokens": self.max_tokens,
            "reasoning_effort": self.reasoning_effort,
            "timeout_s": self.timeout_s,
            "api_key_set": self.api_key is not None,
        }


def to_openai_tools(definitions: list[dict]) -> list[dict]:
    """Wrap provider-neutral {name, description, parameters} tool schemas."""
    return [
        {"type": "function", "function": {
            "name": d["name"],
            "description": d.get("description", ""),
            "parameters": d.get("parameters", {"type": "object", "properties": {}}),
        }}
        for d in definitions
    ]


def parse_arguments(raw):
    """Dict passes through; null/blank remain invalid; JSON text is parsed.
    Anything unparseable is passed through unchanged so the gateway can reject
    and log it, rather than the adapter silently dropping it."""
    if isinstance(raw, dict):
        return raw
    if raw is None:
        return None
    if isinstance(raw, str):
        if not raw.strip():
            return raw
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


# transport(url, body_bytes, headers, timeout_s) -> response text
Transport = Callable[[str, bytes, dict, float], str]


def _urllib_transport(url: str, body: bytes, headers: dict, timeout_s: float) -> str:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout_s) as response:
        return response.read().decode("utf8")


class ModelAdapter:
    """Send messages and tools to the model; return a normalized response."""

    def __init__(self, config: ModelConfig, transport: Transport | None = None) -> None:
        self.config = config
        self._transport = transport or _urllib_transport

    @classmethod
    def from_env(cls, prefix: str = "AGENTSEC_MODEL", role: str = "agent") -> "ModelAdapter":
        return cls(ModelConfig.from_env(prefix=prefix, role=role))

    def describe(self) -> dict:
        return self.config.describe()

    def chat(self, messages: list[dict], tools: list[dict] | None = None,
             *, timeout_s: float | None = None) -> dict:
        """tools are provider-neutral definitions (gateway.tool_definitions()).

        Returns {"content", "tool_calls": [{"id", "name", "arguments"}],
                 "usage", "latency_s", "raw_finish_reason", "raw_message"}.
        """
        cfg = self.config
        request_timeout = cfg.timeout_s if timeout_s is None else min(cfg.timeout_s, timeout_s)
        if request_timeout <= 0:
            raise ModelTimeout("No time remaining for model request")
        body = {"model": cfg.model, "messages": messages, "temperature": cfg.temperature}
        if cfg.seed is not None:
            body["seed"] = cfg.seed
        if cfg.max_tokens is not None:
            body["max_tokens"] = cfg.max_tokens
        if cfg.reasoning_effort is not None:
            body["reasoning_effort"] = cfg.reasoning_effort
        if tools:
            body["tools"] = to_openai_tools(tools)
        headers = {"Content-Type": "application/json"}
        if cfg.api_key:
            headers["Authorization"] = f"Bearer {cfg.api_key}"
        url = f"{cfg.base_url}/chat/completions"

        started = time.monotonic()
        try:
            text = self._transport(url, json.dumps(body).encode("utf8"), headers, request_timeout)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf8", "replace")[:500] if exc.fp else ""
            raise BadModelResponse(f"HTTP {exc.code} from {url}: {detail}") from exc
        except (socket.timeout, TimeoutError) as exc:
            raise ModelTimeout(f"No response from {url} within {request_timeout}s") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (socket.timeout, TimeoutError)):
                raise ModelTimeout(f"No response from {url} within {request_timeout}s") from exc
            raise ModelUnreachable(f"Cannot reach model endpoint {url}: {exc.reason}") from exc
        except (ConnectionError, OSError) as exc:
            raise ModelUnreachable(f"Cannot reach model endpoint {url}: {exc}") from exc
        latency = time.monotonic() - started
        return self._normalize(text, latency)

    @staticmethod
    def _normalize(text: str, latency: float) -> dict:
        try:
            raw = json.loads(text)
            choice = raw["choices"][0]
            message = choice["message"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise BadModelResponse(f"Unexpected response shape: {text[:300]!r}") from exc
        if not isinstance(message, dict):
            raise BadModelResponse(f"Unexpected message: {message!r}")

        tool_calls = []
        for call in message.get("tool_calls") or []:
            fn = call.get("function") if isinstance(call, dict) else None
            if not isinstance(fn, dict) or not fn.get("name"):
                raise BadModelResponse(f"Malformed tool call: {call!r}")
            tool_calls.append({
                "id": call.get("id") or f"call_{uuid.uuid4().hex[:12]}",
                "name": fn["name"],
                "arguments": parse_arguments(fn.get("arguments")),
            })
        content = message.get("content")
        return {
            "content": content if isinstance(content, str) and content != "" else None,
            "tool_calls": tool_calls,
            "usage": raw.get("usage"),
            "latency_s": round(latency, 3),
            "raw_finish_reason": choice.get("finish_reason"),
            "raw_message": message,
        }
