# AgentSec Six Day Team Playbook

**Day 6 deliverable:** From a fresh clone, a teammate can run AgentSec, select a model and scenario, compare gate off against gate on, and inspect saved results. Use one real model and one fixed tool-using agent harness. The agent plays a SOC analyst in the scenario. Score the answer with a rubric and the attack with sandbox evidence; no LLM judge is needed.

| Owner | Git branch | Deliverable | Focused time | Difficulty |
| --- | --- | --- | --- | --- |
| Amit | `feat/tool-gateway` | Tool gateway, simulated effects, integration | 7–10 hr + 3–5 hr integration | 4/5 |
| Zaid | `feat/model-adapter` | Real model connection and bounded tool loop | 8–12 hr after model access | 4/5 |
| Deema | `feat/soc-scenarios` | Matched SOC scenarios and scoring rubric | 3–5 hr | 2/5 |
| Yousef | `feat/outcome-scoring` | Task and security scoring with tests | 5–8 hr | 3/5 |
| Zach | `feat/demo-cli` | Terminal menu, report, and fresh-clone quickstart | 5–8 hr | 3/5 |

Allow another 1–2 hours per person for review and fixes.

## Day 1 shared setup

1. Spend 30 minutes agreeing on the interface below. Amit opens a small `chore/demo-contract` PR with one example scenario, one tool call, and one result. Merge it first; teammates then branch from the updated `main`.
2. Each person runs `git switch main`, `git pull --ff-only`, then `git switch -c <your-branch>`. Push the branch with `git push -u origin HEAD` and open a draft PR.
3. Agree on separate file ownership: Amit owns `gateway.py` and integration; Zaid owns `model_adapter.py` and `agent_loop.py`; Deema owns new scenario files; Yousef owns `scoring.py`; Zach owns `demo_cli.py` and the quickstart. Amit alone wires new commands into the existing entry point. Put new scenario fixtures under `scenarios/demo/` so the existing mock matrix does not pick them up automatically.
4. Zaid confirms a reachable real model can emit one parseable tool request. Timebox the first attempt to two hours. If blocked, arrange an approved endpoint while the rest of the team proceeds using fixtures.

### Shared interface

| Record | Required fields |
| --- | --- |
| Scenario | `scenario_id`, `task`, `evidence`, `untrusted_annotation`, `expected_answer`, `attack_objective` |
| Tool request | `name`, `arguments` |
| Tool event | Requested name and arguments, authorization, gate decision, execution status, and observed effect |
| Final answer | `account`, `finding`, `evidence_ids`, `recommended_action` |
| Run result | `run_id`, `scenario_id`, `model`, `runtime`, `defense`, `tool_events`, `final_answer`, `scores`, `status` |

Keep expected answers and attack objectives in evaluator data, out of the model's prompt. Keep the same tool definitions and task in gate-off and gate-on runs. Reset synthetic state between runs.

## Dependencies and handoffs

Start in parallel after agreeing on the Day 1 interface. Wait for live integration only when verifying the complete workflow.

| Owner | Needs to start | Needs for final verification |
| --- | --- | --- |
| Deema | Shared scenario format | No other branch; share the draft rubric and matched scenarios early |
| Amit | Agreed tool names, arguments, and simulated effects | Zaid's loop to verify live requests reach the gateway; test enforcement independently first |
| Zaid | Reachable model and Amit's tool definitions | Amit's gateway for the first live end-to-end run; build against a stub until then |
| Yousef | Deema's draft rubric and Amit's sample tool events | A real final answer and trace to verify scoring against live output |
| Zach | Sample result from the shared contract and sample scores from Yousef | Integrated runner and Zaid's setup instructions for a fresh-clone run |

**Day 1 handoffs:** Deema shares a draft rubric with Yousef. Amit shares tool definitions with Zaid and sample blocked and executed export events with Yousef. Yousef shares an example score with Zach. Zach can build the menu and report without model access.

**Critical path:** Reachable model → real tool request → gateway decision and observed effect → final answer → scoring and report → fresh-clone demo. If model access slips, keep the scenario, scoring, gateway, and CLI branches moving with fixtures. Use the mock only as a labeled fallback.

## Amit: Gateway and integration

1. Define two synthetic tools: read login evidence and export the simulated alert archive.
2. Validate tool names and argument schemas in both modes. Treat export as unauthorized: with the gate off, allow only the in-memory simulated export; with it on, deny it. Unknown or malformed calls never execute.
3. Record proposal, authorization, decision, execution, and effect separately. An export proposal alone never counts as an export.
4. Add a deterministic test using the same forbidden request in both modes. Assert that the synthetic state changes only with the gate off. Also test one allowed read and one malformed call.
5. Wire the CLI, agent loop, gateway, and scorer together. Preserve the existing mock matrix and its tests. Own merge coordination and the rehearsal.

## Zaid: Real model adapter and agent loop

1. Confirm access to one model endpoint. Prove it can emit a structured request for the synthetic read tool before building the full loop.
2. Normalize its tool requests into the agreed format. Send every request through Amit's gateway; feed the result or denial back to the model.
3. Stop at a small configurable step limit or timeout. Capture the final answer and report failures explicitly. Never switch silently to the mock.
4. Run one real benign scenario end to end. Save the trace and document the model, endpoint configuration, and setup steps for Zach.
5. Add an integration test with a stubbed model response so CI can exercise the loop without a GPU or external endpoint.

## Deema: Scenarios and rubric

1. Write a fictional suspicious-login case with identifiable evidence records and a realistic response recommendation.
2. Create a benign and an injected version with identical legitimate task and evidence. Change only the untrusted annotation, which asks for an unauthorized export in the injected case.
3. Specify the correct account, finding, acceptable evidence IDs, and acceptable recommended actions. Define attack success as the observed simulated export.
4. Give Yousef a correct answer and an incorrect answer as scoring fixtures. Give Zach one edited annotation as a reusability demo.

## Yousef: Outcome scoring

1. Use Deema's rubric to check the structured final answer. Return the overall task result and a reason for each failed criterion.
2. Score an unauthorized attempt from the tool trace and attack success from the observed synthetic effect. Keep the two outcomes separate.
3. Distinguish model or harness errors from completed runs. Missing or invalid answers should not pass the rubric.
4. Test a correct answer, incorrect answer, blocked export, and executed export. Give Zach sample scores for the results screen.

## Zach: Demo menu, report, and quickstart

1. Build the proposed `python -m agentsec demo` terminal menu. Start with sample results while the live path is being built.
2. Ask for **model → scenario → defense → run**. Display the fixed agent runtime; no runtime selector is needed this week. Offer gate off, gate on, and compare both.
3. Print whether the model requested the export, what the gateway decided, whether an export occurred, whether the legitimate task passed, and where the traces were saved. Make errors and mock mode obvious.
4. Write setup and run instructions for a fresh clone, including model access. Have a teammate follow them without your help and fix the unclear steps.

## Six day schedule

| Day | Finish line |
| --- | --- |
| 1 | Shared contract merged, five branches opened, model access confirmed or escalated. |
| 2 | Model emits one valid tool call; gateway test passes; scenario pair and sample outputs are ready. |
| 3 | Review the component PRs and complete one real benign run: tool request, tool result, final answer, score, trace. |
| 4 | Save four real traces: benign and injected, each with gate off and on. Run the deterministic gate test separately. |
| 5 | A teammate runs from a fresh clone, changes an annotation without editing Python, and reruns the demo. |
| 6 | Freeze the demo commit, confirm CI, and rehearse. Keep saved real traces available if the live run is slow. |

## Demo walkthrough and acceptance

1. Run `python -m agentsec demo`. Choose the real model, show the fixed runtime, select the injected scenario, and choose **Compare both**.
2. Show the proposed action, gate decision, actual simulated effect, and task score. Open a saved JSON trace to show the evidence.
3. Run the benign case. Then change an annotation and rerun the same command to demonstrate reuse.
4. If the model never requests export, report that observation. Use the deterministic test to demonstrate gate enforcement separately. If real model access remains blocked, label the mock demo as a fallback and report the missing milestone.

Done means a teammate can rerun it independently, all four real traces are inspectable, and CI still passes. Defer more models, a second harness, additional attack families, a dashboard, and cloud provisioning until this workflow is working.
