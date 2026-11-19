# AgentSec Fixes and Next Steps

Working checklist for Group 39. Prepared November 10, 2026.

### November 12 integration progress

See CURRENT_STATE_AND_HANDOFF.md's verified integration update for current state.
Local uncommitted implementation now integrates the adapter/UI, preserves failed-run
security effects, discovers scoring tests, handles malformed answer lists, and adds
model discovery/testing/selection plus saved annotation variants. Offline checks
pass. Mock browser workflow and connection failure handling were verified. Four
live attempts could not connect to local Ollama; successful live verification is
still outstanding. No commits, merges, pushes, installs or model downloads occurred.

## Demo agreement

Show both the working product and its planned direction. Label every capability by its actual state:

| Label | Meaning and behavior |
| --- | --- |
| Working | Connected to the backend and verified |
| Experimental | Implemented, with limitations or incomplete validation stated |
| Planned | Design preview; disabled and excluded from experiment configurations |
| Mock | Simulated model behavior; never presented as real-model evidence |
| Unavailable | Implemented capability that needs setup or a reachable endpoint |

Planned model and harness controls can appear in a sponsor demonstration. Put their status next to the controls; do not rely only on a spoken disclaimer. Do not generate fabricated traces, successful connections, metrics or results when someone clicks an unfinished control. Keep illustrative design data visibly separate from measured runs.

## Current implementation snapshot

Based on the local checkout and fetched references, not a fresh live GitHub inspection:

- The current branch is feat/local-ui. It contains a local browser interface, mock comparison, run archive and JSON export.
- Fetched main includes the scenarios, gateway and scorer at e852ce4.
- The model-adapter branch contains the review fixes at bc52c68. Real-model execution was not verified by the reviewer, and the adapter is not present on the current UI checkout.
- Gateway, scenario and scorer fixture compatibility was verified. This is not proof of a completed real-model experiment.
- Adapter fixes address action-list formatting, malformed argument preservation and late-reply handling. Automated coverage passed; the live-model test was skipped.

## Priority 0: Make the first complete demo trustworthy

| Owner | Action | Completion check |
| --- | --- | --- |
| Zaid | Pull the adapter fixes, review them, and run benign/injected cases with gate off/on | Four real traces saved with model settings, status, answer and tool events |
| Amit + Zaid | Review PR #4 against main after the gateway merge | Correct base, green CI, reviewed interface and inspectable live-run evidence |
| Amit | After adapter merge, update the UI branch from main and test both execution modes | UI starts, real mode works, mock remains clearly labeled |
| Yousef | Preserve security evidence when a run times out or ends with an invalid answer | A run that exports and later fails still records attack success; task completion remains false or unavailable |
| Yousef + Deema | Verify real-answer scoring and malformed-answer behavior | Good/bad fixtures pass/fail correctly; invalid model output cannot crash scoring |
| Zaid + Amit | Record whether the agent actually received the injected content | Exposed, not exposed, and unknown are distinguishable from attack outcome |
| Zach | Write the setup/run quickstart and verify result labels | Another teammate reproduces the run from a fresh clone |

### Confirmed scoring issue to fix

The current score_run() returns unauthorized_attempt=false and attack_success=false whenever status is not completed, without inspecting tool events. This can hide an export that happened before a later timeout or invalid final answer.

Compute security outcomes from the events regardless of final-answer status. Assess task quality separately. Add a regression case: export executes, then the run times out; the result must retain the export evidence.

## Priority 1: Interactive UI with useful configuration

### Model connections — Amit with Zaid

- [ ] Configure an endpoint and model identifier; keep secrets server-side.
- [ ] Add Test connection with distinct messages for unreachable endpoint, missing model, malformed response and incompatible tool calling.
- [ ] Show a selection of configured models; only list endpoint-discovered models if discovery is supported.
- [ ] Link to the official model page and show concise setup instructions.
- [ ] Record exact checkpoint identity where obtainable, serving backend, template/parser, precision and generation settings.
- [ ] Keep model downloads manual initially. The UI should not silently download large weights or imply that downloading guarantees hardware compatibility.

Done: switch between two configured models without editing Python, and save which configuration actually ran.

### Harness selection — Amit with Zaid

- [ ] Display agentsec-loop-v0 as the implemented runtime.
- [ ] Show OpenClaw/LangGraph as Planned until an adapter is implemented and verified.
- [ ] Add harness capability metadata: tools, memory, retrieval, reset and gateway interception.
- [ ] Validate model/harness combinations before enabling a run.

Done: a selectable runtime actually changes the execution implementation, and its identity is recorded. Do not treat two labels for the same loop as two architectures.

### Scenario and attack editor — Amit with Deema

- [ ] Separate the legitimate task from the untrusted injection field.
- [ ] Start with the existing presets and an editable alert-feed annotation.
- [ ] Show the injection point: note delivered through a successful read tool result.
- [ ] Save edits as a new scenario version; preserve original presets.
- [ ] Keep evaluator-only rubrics and attacker objectives out of model-visible messages.
- [ ] Record scenario content or a stable content hash with every run.
- [ ] Mark ad hoc edited attacks as exploratory; do not quietly pool them with the frozen evaluation set.

Done: a teammate edits an annotation, saves a variant and reruns it without changing code.

### Results and archive — Zach with Yousef

- [ ] Show run status, injection exposure, unauthorized attempt, gateway decision, effect and task score separately.
- [ ] Display tool arguments, returned tool results, final answer and scoring reasons.
- [ ] Distinguish failures and unscored fields from successful defenses.
- [ ] Preserve complete JSON exports and reopen saved runs.
- [ ] Add trial count and a total-run estimate before launching batches.

Done: the report is enough to explain an outcome without reading Python.

## Priority 2: Strengthen the experiment

| Work | Owner proposal | Acceptance condition |
| --- | --- | --- |
| Scenario-driven scoring | Yousef + Deema | Evidence IDs, minimum evidence count and allowed actions come from structured rubric fields rather than case-specific hardcoded rules |
| Less trivial tool misuse | Amit + Deema | Include a permitted tool misused through arguments or data scope, with matched benign control |
| Literature grounding | Deema + team | Link each scenario to its source paper/report and document adaptations; do not claim the original scenario was reproduced exactly without doing so |
| Second real harness | Zaid + Amit | Equivalent tasks and tools, complete gateway coverage, reliable reset and separate runtime identity |
| Model size coverage | Team + sponsor | Define small/medium/large checkpoints and clarify one per tier versus multiple sizes per family |
| Pilot-based sample size | Yousef + team | Report variability, denominators and the reason for trial counts; five trials remain an initial plan |
| Reproducibility | Zach + team | Pin relevant versions, save configuration, control state reset and verify the rerun procedure |
| Compute request | Amit + team | Specify selected model precision/context, GPU memory, host RAM, storage, runtime estimate and funding owner |

Comparing different families at different sizes does not isolate the effect of size. Use within-family comparisons for size claims, or describe results as comparisons of the specific configurations.

## Defer until the workflow works

- Desktop installer and automatic model management.
- Public hosting, accounts and paid dashboard subscriptions.
- Adding many untested runtime/model combinations.
- LLM judging where deterministic effect checks already answer the question.

## Team review rules

1. Open PRs early, using Draft for unfinished work.
2. Keep each PR focused and identify dependencies.
3. Require CI plus a teammate review before merging.
4. Test interfaces together; passing each component's own tests does not prove integration.
5. Preserve evidence of failed runs and unsuccessful attacks.
6. Update this checklist as work is verified. Planned features must not become Working merely because their UI is present.

## Next demonstration

Launch the local UI, show the available model and runtime, choose a preset, inspect/edit its annotation, and compare gate off/on. Open the trace and explain the attempted action, actual effect and task score. Reopen the saved record and export it.

If the attack does not persuade the model, report that observed outcome. Demonstrate gateway enforcement separately with the deterministic test. A future-feature preview is acceptable when clearly separated from these measured results.
