# AgentSec proposal and requirements

Prepared November 19, 2026 for Group 39.

This document summarizes what the original sponsor documents, proposal presentations, and later meeting feedback ask the team to deliver. It separates requirements from proposed implementation choices. It does not certify that a requirement has been completed.

Use this document to check scope. Use `RESEARCH_READINESS_PLAN.md` for assignments, dependencies, implementation work and acceptance checks. Those are different purposes.

## 1. What the project is supposed to produce

AgentSec is a reusable, sandboxed platform for evaluating and hardening tool-using LLM agents. It must support controlled attacks, multiple model families and agent architectures, security defenses, automated experiments, outcome measurement and reproducible results.

The project includes both engineering and research: a functioning testbed and a defensible evaluation of how agent systems fail, how attacks transfer, and what defenses preserve legitimate task performance. A dashboard by itself, a collection of prompts, or a single successful injection does not fulfill that scope.

The original documents use the name **AgentSecBench**. The team now uses **AgentSec** following sponsor naming guidance. The name change does not by itself change the technical requirements.

## 2. Sources and how to interpret them

| Reference | Source | What it establishes |
| --- | --- | --- |
| S1 | `ValixAI - AgentSecBench - RFP.docx` | Sponsor objectives, required deliverables, constraints, research questions and minimum technical scope |
| S2 | `ValixAi - AgentSecBench - Nomination.docx` | Two-semester project summary, major deliverables and resource expectations; identifies required versus desired deliverables |
| S3 | 20-slide `GMU CYSE492 Proposal Template Fall2026_v2-2 (1) - Copy.pptx` | Revised proposal preceding the later sponsor-discussion deck; initial evaluation matrix, architecture and methodology |
| S4 | Older 32-slide `GMU CYSE492 Proposal Template Fall2026_v2-2 (1) (1).pptx` | Earlier expanded size coverage, detailed dated schedule and work breakdown |
| S5 | Sponsor/faculty meeting notes supplied by Amit in this chat | Subsequent size/resource guidance, faculty requests for measurable implementation progress, and November 19 automation feedback |
| S6 | 11-slide `AgentSecBench_Group39_Sponsor_Deck.pptx`, inspected November 19 | Latest identified sponsor scope-discussion deck: same minimum matrix, milestone windows and decisions seeking approval |

S1 and S2 are in `C:/Users/omika/Downloads/proposal/proposal/tmp/`. S3, S4 and S6 are in `C:/Users/omika/Downloads/`.

**Source precedence:** retain S1/S2 as the written requirement baseline until a recorded sponsor/faculty decision changes it. Use S6 as the latest identified presentation of the team's proposed direction; S3/S4 provide earlier context. Explicit approved amendments govern their affected commitments, but none should be inferred merely because a deck is newer. S5 is user-reported meeting evidence, not a signed amendment. A slide seeking approval is not evidence of approval.

S6 slide 10 stages Fall as a working beta with a first attack/defense and Spring as expansion/evaluation, whereas S1 explicitly requests six representative families by the end of Fall. This scope/timing conflict needs a recorded decision. S6 uses milestone windows and expressly says to reconcile older exact dates; dates below remain historical planning entries.

## 3. Original sponsor requirements

### 3.1 Platform and evaluation coverage

| ID | What is being asked for | Source |
| --- | --- | --- |
| P1 | A containerized, sandboxed evaluation harness/testbed | S1 Objectives and Codebase deliverable; S2 |
| P2 | At least six representative agentic-security attack families, with machine-readable experiment logging, by the end of Fall | S1 Objectives |
| P3 | At least three LLM/model families | S1 Objectives and Technical Specifications; S2 |
| P4 | At least two agent architectures/frameworks or orchestration patterns | S1 Objectives and Technical Specifications; S2 |
| P5 | A common benchmark/protocol across the selected systems | S1 Objectives and Technical Specifications |
| P6 | Repeated trials sufficient to report variability rather than isolated anecdotes | S1 Technical Specifications; S2 |
| P7 | At least three mitigation strategies, including least privilege/action gating | S1 Objectives and Defense Evaluation; S2 |
| P8 | Measure both security benefit and legitimate-task utility/cost impact under matched benchmark conditions | S1 Defense Evaluation |
| P9 | Automated experiment execution, configurable scenarios, model/agent adapters, structured logs and tests | S1 Codebase and Sandboxed Testbed deliverable |
| P10 | Setup documentation and a reproducibility script/package usable by another team | S1 Codebase/Specification deliverables; S2 |

“Three model families” means different model lineages, not three sizes of one family. “Two architectures/frameworks” requires two actual implemented execution systems or orchestration patterns, not two dropdown labels pointing to the same loop.

### 3.2 Six minimum attack families

These categories come from S1's Technical Specifications appendix. The six-family grouping is in the original RFP; it was not invented for the dashboard or generated as a replacement for OWASP.

| Family | Required scope |
| --- | --- |
| 1. Direct instruction/prompt manipulation | Adversarial instructions directed at the agent |
| 2. Indirect prompt injection | Instructions arriving through retrieved or tool-supplied content |
| 3. Retrieval/context and memory poisoning | Manipulated retrieved context and persistent or session memory |
| 4. Cross-agent manipulation | Message manipulation, role confusion or trust-boundary abuse between agents |
| 5. Tool/permission misuse | Unsafe parameters, unauthorized actions or permission abuse |
| 6. Synthetic disclosure or unsafe execution | Synthetic secret/data disclosure or unsafe output-to-action/code execution inside the sandbox |

The third category explicitly names both retrieval/context and memory. Coverage should distinguish those mechanisms. The sixth category allows alternatives; the wording does not require unrestricted real host-code execution.

Multiple annotation phrasings on one SOC case do not automatically demonstrate all six families. A note claiming another agent approved an action does not establish that the software has an actual cross-agent message surface.

### 3.3 Mitigations

The sponsor requires at least three controls. One must address least privilege or action gating. S1 lists examples for the additional controls:

- Context provenance/isolation.
- Input or retrieval filtering.
- Independent policy verification.
- Human approval for high-impact actions.
- Equivalent defenses addressing the stated risks.

These examples are not a requirement to implement every listed defense. The current engineering plan proposes action gating, context isolation/provenance and independent policy verification. That selection is an implementation decision; the original requirement is three meaningful controls evaluated for security and utility.

### 3.4 Required measurements

| Area | Metrics named in S1/S2 |
| --- | --- |
| Security | Attack success; unauthorized action rate; synthetic-secret disclosure; containment/recovery |
| Utility | Normal task completion; false blocking/refusal; latency; token/API cost and operational overhead |
| Reporting quality | Aggregate statistics, variability, failure examples and limitations/threats to validity |

The implementation needs explicit definitions, denominators and evidence for each metric. A proposed action is different from an executed effect. An invalid tool call is different from a permission denial. A completed model response is different from a correct legitimate-task answer.

Do not report missing measurements as zero. Explain when a metric is not applicable to a scenario. Broader disclosure/recovery claims require scenarios and oracles that actually measure those outcomes.

### 3.5 Safety and reproducibility constraints

S1/S2 require:

- Sponsor-approved isolated local, virtual, containerized or cloud lab environments; the harness itself is to be containerized.
- Synthetic credentials/secrets/data and public or sanitized inputs; intentionally vulnerable or simulated applications/services where appropriate.
- No attacks against production systems, customer environments or unrelated third parties.
- No reliance on proprietary Valix data, NDAs or restricted information; compatibility with GMU public-project rules.
- Documented safety/ethics boundaries and relevant disclosure considerations before experiments.
- Sufficient methodological detail, code, configuration and artifacts for independent reproduction.

These are project constraints reported from the documents, not instructions in this file to provision services or publish data automatically.

## 4. Research questions

S1 Technical Specifications and S3 slide 4 ask the team to investigate:

1. Which agent capabilities and trust boundaries increase the likelihood or severity of security failures?
2. How transferable are attacks across model families and agent architectures?
3. Which mitigations reduce attack success while preserving task performance and acceptable cost/latency?

The final experiments and paper should connect results to these questions. A size comparison alone does not answer them. A study that changes model, runtime, scenario and budget simultaneously cannot cleanly attribute differences to one factor.

The readiness plan maps each question to controlled comparisons and limits on claims; completing every matrix cell alone does not answer every question.

## 5. What the revised proposals add or make concrete

### 5.1 Initial evaluation matrix

S3 slides 12/14 and S6 slide 8 propose:

| Dimension | Initial proposal |
| --- | --- |
| Model coverage | Three open-source model families, initially one practical checkpoint/size from each |
| Architectures | Two |
| Attack families | Six |
| Security configurations | Unprotected baseline plus three mitigations: four conditions total |
| Repetitions | Five initial trials per configuration, with pilot findings used to reassess adequacy |
| Total | 144 configurations and approximately 720 attack-test episodes |

The arithmetic assumes one representative scenario per family and all combinations supported. Additional scenario instances, checkpoints, defense combinations and trials increase the count. Benign controls, pilots, retries and adaptive attacker evaluations are additional work.

Five is a proposal starting count, not an RFP guarantee of statistical adequacy. The RFP requires enough repetition to estimate variability.

### 5.2 Architecture and product behavior

S3 slides 5, 6 and 8 describe:

- An orchestrator coordinating configuration and repeated experiments.
- Interchangeable model and agent-framework adapters.
- An attack injection engine covering prompts, retrieval, memory and tool responses.
- A sandbox with simulated tools and synthetic data.
- Configurable security controls.
- Logging/evaluation that produces reports and benchmark data.
- A user workflow selecting model, agent architecture, attack and defense before execution.

The SOC analyst is a reference agent-under-test scenario, not the definition of the whole product. A separate LLM judge is not mandated by these documents. Outcome evaluation can use validated deterministic oracles where appropriate.

S4's CONOPS also describes tables, plots, failure examples, command/configuration-based execution and documented extension points. S3's stated reusable-platform goal is compatible with a local browser UI; it does not require public SaaS hosting or a downloadable desktop installer.

## 6. Required deliverables and timing

| Period | Required deliverable | Source |
| --- | --- | --- |
| Late Fall | Threat/system model, attack taxonomy, benchmark scenarios/specification, experimental protocol, safety boundaries, metrics and baseline plan | S1 Specification deliverable; S2; S3 slide 17 |
| End of Fall | Containerized harness with six representative families and machine-readable logging | S1 Objectives |
| Late Fall beta; Late Spring final | Version-controlled testbed, automated execution, scenario configuration, adapters, tests, setup instructions and reproducibility script | S1 Codebase deliverable; S2 |
| Late Spring | Cleaned results dataset, quantitative analysis, defense comparison, feasible ablations/sensitivity analysis and threats to validity | S1 Research Package deliverable |
| Mid/Late Spring according to course/sponsor schedule | IEEE-format paper, poster, competition/demo materials and sponsor-reviewed submission-ready manuscript/reproducibility package | S1 course/sponsor deliverables; S2 |
| Late Spring | Practical hardening guide translating measured findings into engineering recommendations | S1 Practical Hardening Guide |

S1 also lists biweekly customer reporting, weekly mentor activity reporting, a Late Fall faculty review and Late Spring sponsor acceptance. Confirm exact course submission dates with faculty.

S2 identifies a sanitized open-source release subject to license/GMU/sponsor approval and external manuscript submission as desired deliverables. A reusable, shareable research package is required; public release and venue submission need their respective decisions. Peer-review acceptance is explicitly outside the team's control.

### Dated entries from the older presentation

These are S4 proposal schedule entries, not newly verified official deadlines:

| Date | Entry |
| --- | --- |
| October 21, 2026 | Sponsor threat model/taxonomy/requirements review |
| November 4, 2026 | Sponsor architecture/CONOPS/framework/model-selection review |
| November 18, 2026 | Sponsor initial scenarios/protocol review |
| November 26, 2026 | Group beta setup and first attack scenario test |
| December 2, 2026 | Group Fall package/baseline summary and sponsor Fall beta review |
| December 4, 2026 | Separate beta/mid-term date on slide 29; conflicts with December 2 review timing |
| February 2, 2027 | Sponsor baseline results/final matrix review |
| February 16, 2027 | Sponsor defenses 2/3 and comparative-testing review |
| March 2, 2027 | Sponsor full model/framework results and preliminary analysis |
| March 17, 2027 | Sponsor metrics/reproducibility review |
| March 31, 2027 | Sponsor benchmark/paper/poster/hardening-guide review |
| April 8, 2027 | Group draft IEEE paper, poster and hardening guide |
| April 22, 2027 | Group final demo/documentation/results |

S4 slide 29 also describes final acceptance in Late Spring around May, and slide 23 has an incomplete April sponsor date. Resolve calendar inconsistencies rather than treating every entry as a separate confirmed deadline. S3 uses Late Fall/Spring without a comparable dated schedule.

## 7. Later sponsor and faculty feedback

This section reflects S5, separate from the original written requirements.

| Feedback | Consequence / unresolved point |
| --- | --- |
| Sponsor wants small, medium and large models and diversity of families/environments | Select exact checkpoints and size definitions. Determine whether three total checkpoints spanning tiers is sufficient or whether three sizes per family are expected |
| Sponsor described gpt-oss-20b working on a 64 GB Mac and 120b crashing; considers 120b large | Anecdotal resource guidance, not a hardware acceptance test or a mandatory checkpoint selection |
| Cloud VM/SSH route is possible; approximately 1 TB storage discussed | Resource planning guidance, not proof of enough GPU memory or compute budget |
| Valix declined financial support; pursue GMU resources | Original RFP funding expectations need updating. No confirmed VM purchase or budget follows from the earlier $250–$300 discussion |
| Faculty requests a measurable written plan with named owners and concrete progress | Maintain tasks, completion evidence and demonstrated software rather than presentation-only progress |
| Faculty requests scenarios 1/2/3 tied to source papers/reports | Deliver at least three sourced case specifications and explain adaptations; six-family coverage still remains in the RFP |
| Faculty requests an experiment design specifying models, tokens and compute | Supply a concrete manifest and pilot-based resource estimate before requesting funding |
| Faculty notes mention OpenClaw | Confirm whether that specific framework is required; S1 does not mandate it |
| November 19 sponsor feedback emphasizes automation | Automated execution is already in S1. The team additionally agreed to plan one bounded response-driven attacker; confirm that interpretation with Dr. Baye |

## 8. Automation scope

**Original written requirement:** automated experiment execution. Configurations should drive scenario injection, trials, logging and evaluation without manually operating each run.

**Additional agreed engineering scope:** fixed-suite campaigns plus one adaptive attacker for the current tool-response annotation surface. The adaptive attacker generates/revises payloads from permitted target observations, within recorded attempt/time/token budgets. It has a separate readiness gate: a validated frozen fixed-suite campaign may proceed while adaptive work matures. This is documented in `RESEARCH_READINESS_PLAN.md`; it is not an explicit original RFP mandate.

Keep fixed attacks and adaptive attack episodes distinguishable in the dataset and analysis. An adaptive attacker is not automatically another architecture under test, a separate seventh attack family, or evidence that every surface supports automated adaptation.

## 9. Decisions still needed

- [ ] Final model checkpoint count, family/size coverage and whether size effects are a research claim.
- [ ] Second runtime/framework and whether faculty specifically expects OpenClaw.
- [ ] Exact scenario instances and supported runtime/capability cells; treatment of unsupported combinations.
- [ ] Three chosen mitigation implementations and whether combinations/ablations are in the initial study.
- [ ] Trial counts after pilots and analysis/uncertainty methods.
- [ ] Whether the proposed bounded adaptive attacker satisfies Dr. Baye's intended automation scope.
- [ ] Confirmed resource access, budget/payer and fallback if large models cannot run.
- [ ] Official calendar and resolution of older presentation date conflicts.
- [ ] Final taxonomy mapping, if OWASP is used, and any sponsor-approved scope amendments.

OWASP mapping can help communicate coverage. Neither OWASP Top 10 coverage nor replacing the six RFP families is established as a requirement by these supplied documents. Map taxonomies explicitly; seek a recorded scope decision before dropping a required family.

## 10. What is a recommendation rather than an original requirement

The cream/serif visual style, specific graphs, local browser implementation, named team assignments, exact branch names, bounded adaptive-attacker defaults, candidate framework choice, Ollama, a particular VM, and the proposed December research-readiness target are engineering choices or later recommendations. They should serve the source requirements but must not be attributed to the RFP as mandates.

The original documents allow open-source libraries and favor reproducible academic use. They do not establish a universal ban on paid infrastructure or require a purchased software stack. Budget and model licensing/access remain explicit project decisions.

## 11. Completion standard

The project is complete when the team can demonstrate the required platform capabilities, produce the declared cross-model/cross-runtime defense evaluation with valid measurements, and deliver the reproducible dataset, paper/poster, hardening guide and sponsor/course artifacts. Passing CI alone verifies only the checks implemented in CI; it does not establish research coverage or empirical findings.

For the work required to get there, follow `RESEARCH_READINESS_PLAN.md`. For any change to the scope summarized here, record the source, date, decision and approving stakeholder rather than silently editing the baseline.

For substantive deviations, record **baseline → change → reason → expected benefit → cost → validation → decision owner/status**. Ordinary reversible implementation choices do not need the same approval process as dropping a deliverable, changing an agreed deadline or reducing promised study coverage.
