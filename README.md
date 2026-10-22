# AgentSec — Milestone 0: Trace-First Action Boundary Prototype

> **Status: infrastructure proof of concept only.** Uses a deterministic, rule-based mock agent — **NOT a real LLM**. The mock intentionally follows a marker in an attacker-controlled alert so we can validate how proposals, permissions, execution decisions, and utility metrics are logged. **No model-vulnerability claims are supported by these results.**

## Goal / sponsor alignment

AgentSec is Group 39's Valix.ai-sponsored GMU CYSE 492/493 project: a reproducible, sandboxed red-team + hardening testbed for tool-using LLM agents. The required final study covers six attack families, at least three model families, two agent architectures, three defenses, and security-versus-utility evaluation. This prototype only demonstrates the **action-boundary and experiment trace contract** for one SOC-alert workflow.

## What works now

- Two versioned local synthetic scenarios: benign alert and indirect-injection alert.
- A deliberately vulnerable **mock decision generator** that proposes tool actions.
- A runtime action gate: `off` (no enforcement) and `gate` (allowlisted tools only).
- A complete trace of proposed tool calls, their provenance, authorization and execution decisions.
- Security **and** legitimate-task metrics in each result.
- Deterministic run IDs, unit tests, Docker, and GitHub Actions CI.

All tool effects are simulated. Nothing is sent over the network, executed in a shell, or exposed outside the harness.

## Run locally (Python 3.10+; no third-party packages)

```bash
python -m unittest discover -s tests -v
python -m agentsec matrix --out artifacts/matrix.json
python -m agentsec run --scenario scenarios/02_soc_injected.json --defense gate --out artifacts/guarded.json
```

Review `artifacts/matrix.json` and inspect `trace[]` for the tool proposal, content origin, policy decision, and whether simulated execution occurred.

## Docker (Docker Desktop must be running)

```bash
docker build -t agentsec:milestone0 .
docker run --rm --network none --read-only agentsec:milestone0
```

The container runs as a non-root user, with no network and a read-only filesystem. CI also builds and runs it. Host trace exports can be generated with the Python CLI, or via a separately mounted output directory in future milestones.


## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Experimental protocol and metrics](docs/PROTOCOL.md)
- [Development roadmap and acceptance criteria](docs/ROADMAP.md)
- [Existing frameworks and open comparison questions](docs/RELATED_WORK.md)

## Out of scope for Milestone 0

No real agent/model integrations, no measured prompt-injection success rate, no external API, no cloud, no Kubernetes, no dashboard, no production targets. Future runs use only approved synthetic data and sandboxed tools.
