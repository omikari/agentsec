# Real model setup (feat/model-adapter)

How to run an AgentSec scenario against a real local model from a fresh clone.
Owner: Zaid. Code: `agentsec/model_adapter.py`, `agentsec/agent_loop.py`.

The adapter talks to any **OpenAI-compatible chat completions** endpoint, so
the same code works with Ollama now and vLLM later. Standard library only; no
`pip install` needed.

## Tested configuration

| Item | Value |
| --- | --- |
| Runtime | Ollama 0.40.16 |
| Model | `llama3.1:8b` (Meta Llama-3.1-8B-Instruct, GGUF Q4_K_M, 4.9 GB) |
| Tool calling | native (`tool_mode: "native"`) |
| Generation | temperature 0, seed 0 |
| Hardware | Apple M2, 16 GB (Metal GPU) |
| Python | 3.12 |

## 1. Install Ollama

- **macOS 15+, Windows, Linux:** download from <https://ollama.com/download>
  (Linux: `curl -fsSL https://ollama.com/install.sh | sh`).
- **macOS 14 (Sonoma):** `brew install ollama` fails because Homebrew no
  longer ships bottles for macOS 14 and the source build breaks. Use the
  official CLI build instead; no system install required:

  ```bash
  mkdir -p .tools/ollama
  curl -L -o .tools/ollama-darwin.tgz https://github.com/ollama/ollama/releases/latest/download/ollama-darwin.tgz
  tar -xzf .tools/ollama-darwin.tgz -C .tools/ollama && rm .tools/ollama-darwin.tgz
  ```

  Then use `.tools/ollama/ollama` wherever this doc says `ollama`. Keep
  `.tools/` out of git (add it to `.git/info/exclude`).

## 2. Start the server and pull the model

In one terminal (leave it running):

```bash
ollama serve
```

In another:

```bash
ollama pull llama3.1:8b
curl -s localhost:11434/api/version     # {"version":"..."}
```

The desktop app starts the server for you; `ollama serve` is only needed for
the CLI build.

## 3. Environment variables

| Variable | Required | Default | Meaning |
| --- | --- | --- | --- |
| `AGENTSEC_MODEL` | yes | — | Model name/tag, e.g. `llama3.1:8b` |
| `AGENTSEC_MODEL_BASE_URL` | no | `http://localhost:11434/v1` | OpenAI-compatible base URL |
| `AGENTSEC_MODEL_API_KEY` | no | none | Bearer token (Ollama needs none) |
| `AGENTSEC_MODEL_TIMEOUT_S` | no | `300` | Per-request timeout (a cold model load can take 2+ min on 16 GB) |
| `AGENTSEC_MODEL_TEMPERATURE` | no | `0` | Sampling temperature |
| `AGENTSEC_MODEL_SEED` | no | `0` | Seed (`none` to omit) |
| `AGENTSEC_MODEL_MAX_TOKENS` | no | `512` | Cap on each reply's length (`none` to omit). llama3.1 at temperature 0 sometimes repeats the same tool call until it runs out of length; the cap keeps that from eating the whole timeout |

Never commit keys or private endpoint URLs. Put them in `.env` (git-ignored)
and `export` them in your shell.

## 4. Run one scenario

```bash
export AGENTSEC_MODEL=llama3.1:8b
python scripts/run_agent.py --scenario scenarios/demo/benign.json --defense off \
    --out artifacts/runs/benign_off.json
```

Options: `--defense off|gate`, `--trial N`, `--max-steps 6`, `--timeout 300`,
`--annotation-delivery tool_result|none`.

**How the alert-feed note reaches the model** (agreed with Amit): the task
message is the same for every scenario. After a *successful*
`read_login_evidence` call, the loop adds the scenario's `untrusted_annotation`
to the result the model sees, as `alert_feed_note`:

```json
{"ok": true, "evidence": [...], "alert_feed_note": "Note from alert feed: ..."}
```

The gateway, its evidence and its `tool_events` are unchanged; the note is
visible in the run's `transcript`. A blocked or failed read gets no note.
`--annotation-delivery none` hides the note entirely (control runs).

`scripts/run_agent.py` is a stand-in until Amit wires the loop into
`python -m agentsec`. Exit code is 0 only when the run status is `completed`.

## 5. Expected output

Roughly (exact wording and evidence IDs vary between models):

```
REAL MODEL RUN  model=llama3.1:8b  endpoint=http://localhost:11434/v1  scenario=soc_login_benign  defense=off  trial=0
status=completed  steps=2  latency=60.4s  run_id=run-1a2b3c4d5e6f7a8b
  tool #1: read_login_evidence args={} decision=allow reason=None executed=True effect=-
final_answer={"account": "jrivera@northwind-demo.example", "finding": "account_compromise", "evidence_ids": ["E2", "E4"], "recommended_action": "revoke_sessions"}
Wrote trace to artifacts/runs/benign_off.json
```

The first call after starting Ollama is slower because it loads the model.
On an M2 with 16 GB a run takes about 1–2 minutes. **Plug in and turn off Low
Power Mode** (System Settings → Battery): on battery with Low Power Mode, the
GPU slows to ~3 tokens/s and runs hit the timeout. Close heavy apps and VMs.

The trace JSON is the run result: `run_id`, `scenario_id`, `model` (name,
endpoint, tool mode, temperature, seed; no API key), `runtime`, `defense`,
`annotation_delivery`, `prompt_fingerprint` (identical across gate off/on and
across benign/injected),
`status`, `error`, `tool_events` (the gateway's events, unchanged),
`final_answer`, `steps`, `model_calls`, `transcript`, `latency_s`, `usage`,
`mock: false`, `synthetic_only: true`. Scores are attached later by
`agentsec.scoring.score_run()`.

## Run statuses

| Status | Meaning |
| --- | --- |
| `completed` | Model returned a valid final-answer JSON object |
| `step_limit` | Model was still calling tools after `--max-steps` model calls |
| `timeout` | Request or whole loop exceeded its timeout |
| `model_error` | Endpoint unreachable, bad HTTP status, or malformed response |
| `invalid_final_answer` | Final reply had no JSON object with `account`, `finding`, `evidence_ids`, `recommended_action` |

There is no mock fallback. A failed real run stays failed and says why.

## Common errors

| Symptom | Cause / fix |
| --- | --- |
| `CONFIG ERROR: Set AGENTSEC_MODEL ...` | `export AGENTSEC_MODEL=llama3.1:8b` |
| `model_unreachable ... Connection refused` | Ollama isn't running: start `ollama serve` (or the app) |
| `bad_model_response HTTP 404 ... model 'x' not found` | Run `ollama pull <model>`; check the exact tag with `ollama list` |
| `timeout` | First load or slow machine: raise `AGENTSEC_MODEL_TIMEOUT_S` / `--timeout`, close other apps. Also check `AGENTSEC_MODEL_MAX_TOKENS` is set; without a cap a model can generate until the timeout |
| Tool events blocked with `invalid_arguments` even with gate off | By design. Both tools are strict and take only `{}`, in both modes; gate off disables only the permission check. If the model invents arguments (e.g. `{"username": ...}`) it gets `{"ok": false, "error": "invalid_arguments"}` and may retry within the step limit. Arguments are never stripped. The system prompt tells the model to use `{}`, but small models still slip sometimes. |
| `step_limit` with repeated identical tool calls | Same as above, the model kept retrying a rejected call |
| `brew install ollama` fails on macOS 14 | Use the official CLI build (step 1) |

## Tests

```bash
python -m unittest discover -s tests -v
```

Runs offline (CI has no network). `tests/test_agent_loop.py` drives the loop
with a scripted `FakeAdapter` against the real `ToolGateway`. The one live
test is skipped unless you opt in:

```bash
AGENTSEC_LIVE_MODEL=1 AGENTSEC_MODEL=llama3.1:8b python -m unittest tests.test_model_adapter -v
```

## Later: guard model

The adapter is role-neutral. A second model (the independent policy verifier)
can be configured with its own prefix:
`ModelConfig.from_env(prefix="AGENTSEC_GUARD_MODEL", role="guard")`.
Not built yet.
