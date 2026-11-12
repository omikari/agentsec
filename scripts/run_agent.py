"""Run one scenario through the real model + ToolGateway and save the trace.

Temporary entry point for the model adapter branch. Amit owns wiring this into
`python -m agentsec`; until then use:

    AGENTSEC_MODEL=llama3.1:8b python scripts/run_agent.py \
        --scenario scenarios/demo/benign.json --defense off \
        --out artifacts/runs/benign_off.json

Exit code 0 only when status is "completed". There is no mock fallback.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentsec.agent_loop import ANNOTATION_DELIVERY, DEFAULT_ANNOTATION_DELIVERY, run_agent  # noqa: E402
from agentsec.model_adapter import ModelAdapter, ModelError  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="AgentSec real-model run (one trial)")
    p.add_argument("--scenario", required=True, help="Scenario JSON, e.g. scenarios/demo/benign.json")
    p.add_argument("--defense", choices=["off", "gate"], required=True)
    p.add_argument("--out", help="Write the full run result JSON here")
    p.add_argument("--trial", type=int, default=0)
    p.add_argument("--max-steps", type=int, default=6)
    p.add_argument("--timeout", type=float, default=300.0, help="Whole-loop timeout in seconds")
    p.add_argument("--annotation-delivery", choices=ANNOTATION_DELIVERY, default=DEFAULT_ANNOTATION_DELIVERY)
    args = p.parse_args()

    scenario = json.loads(Path(args.scenario).read_text(encoding="utf8"))
    try:
        adapter = ModelAdapter.from_env()
    except ModelError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2

    meta = adapter.describe()
    print(f"REAL MODEL RUN  model={meta['name']}  endpoint={meta['base_url']}  "
          f"scenario={scenario['scenario_id']}  defense={args.defense}  trial={args.trial}")
    result = run_agent(scenario, args.defense, adapter, max_steps=args.max_steps,
                       timeout_s=args.timeout, trial=args.trial,
                       annotation_delivery=args.annotation_delivery)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")

    print(f"status={result['status']}  steps={result['steps']}  latency={result['latency_s']}s  "
          f"run_id={result['run_id']}")
    for e in result["tool_events"]:
        effect = e["effect"]["type"] if e["effect"] else "-"
        print(f"  tool #{e['sequence']}: {e['name']} args={json.dumps(e['arguments'])} "
              f"decision={e['decision']} reason={e['reason']} executed={e['executed']} effect={effect}")
    if result["final_answer"] is not None:
        print(f"final_answer={json.dumps(result['final_answer'])}")
    if result["error"]:
        print(f"ERROR {result['error']['type']}: {result['error']['message']}", file=sys.stderr)
    if args.out:
        print(f"Wrote trace to {args.out}")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
