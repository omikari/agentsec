# Existing frameworks — gap analysis to verify with sponsor

- **AgentDojo** (https://github.com/sequrity-ai/agentdojo-benchmark): dynamic benchmark for LLM-agent prompt-injection attacks and defenses; already has meaningful overlap.
- **Microsoft PyRIT** (https://github.com/microsoft/PyRIT): open-source, extensible AI red-teaming, with scenarios, scorers, orchestration, and agent-testing capabilities including RAMPART.

## Proposed engineering hypothesis, not a novelty claim

AgentSec can emphasize **tool-action provenance, allow/block decisions at execution boundaries, paired defense comparisons, and normal-task utility tradeoffs** in controlled SOC-style workflows, with a fully reproducible experiment export. Existing tools may already implement subsets or all of these features: conduct a side-by-side feature and workflow comparison before claiming a unique contribution or building custom equivalents.

## Evaluation questions to answer

1. Can AgentDojo represent our SOC workflow and all six sponsor attack families without intrusive modification?
2. Can PyRIT/RAMPART capture proposed and executed tool calls, policy decisions and false blocking as first-class outcomes?
3. Is a thin integration layer or plugin a better engineering contribution than another generic runner?
4. What is the smallest demonstrable contribution the sponsor will recognize as useful and novel?

**Decision gate:** after reviewing at least one hands-on exercise with each tool, document build-versus-extend with concrete evidence, not assumptions.
