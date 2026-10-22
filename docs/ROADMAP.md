# Strict delivery roadmap — 2026–27

## Milestone 0 — meeting demonstrator (now)

**Exit criteria**: repo documented; one runnable synthetic attack/control pair; defense off/on; trace + outcomes exported as JSON; passing tests; container build; CI workflow green after push. Proof is execution traces, not just README screenshots.

## Milestone 1 — actual agent (next)

- Choose one approved model/runtime and one tool-using agent architecture. Avoid introducing all model families at once.
- Replace `mock-marker-v0` with a real model/agent adapter; keep the same scenario and trace schema.
- Implement the SOC triage's two mock tools behind a central enforceable gateway. Never permit raw unmediated tool calls.
- Show a **real observed** example, not a guaranteed successful prompt injection. Include a separate normal-task trial.
- Record model/runtime versions, prompt templates, seeds where supported, and run metadata.

## Milestone 2 — Fall beta

- Add scenario adapter contracts for six RFP attack families.
- Introduce context-provenance and independent policy-check defense states in addition to no defense and the action gate.
- Deliver first containerized repeatable model runs, structured logs, rerun script, and documented threats to validity.

## Milestone 3 — Spring comparative study

- Scale to at least 3 model families × 2 architectures × 6 attack families × 4 defense states; use repeated trials and report variability.
- Prior deck estimate: 144 configurations × 5 trials = 720 attack episodes under one canonical scenario per family, **plus benign utility controls**; confirm study design and compute budget with sponsor.
- Quantify attack success, action attempts/executions, synthetic-secret disclosure, legitimate task completion, false blocking, latency and cost (where measurable).
- Produce reproducibility package, defensible comparisons, hardening guide, IEEE paper and poster.

## Do not build yet

No Kubernetes, cloud account provisioning, web dashboard, SaaS auth, database cluster, or high-complexity multi-agent orchestration until the core agent/tool/policy/scoring loop works and sponsor approves budget.
