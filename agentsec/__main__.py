"""CLI: python -m agentsec matrix|run."""
import argparse
import json
from pathlib import Path
from .core import load_scenario, run_matrix, run_scenario


def main() -> None:
    parser = argparse.ArgumentParser(description='AgentSec MOCK Milestone 0')
    subs = parser.add_subparsers(dest='command', required=True)
    matrix = subs.add_parser('matrix', help='Run every local mock scenario with guard off/on')
    matrix.add_argument('--scenarios', default='scenarios')
    matrix.add_argument('--out', help='Write complete results to a JSON file')
    single = subs.add_parser('run', help='Run one local mock scenario')
    single.add_argument('--scenario', required=True)
    single.add_argument('--defense', choices=['off', 'gate'], required=True)
    single.add_argument('--out', help='Write result to a JSON file')
    args = parser.parse_args()
    if args.command == 'matrix':
        results = run_matrix(Path(args.scenarios))
        output = {"mode": "mock_demo", "count": len(results), "results": results}
    else:
        output = run_scenario(load_scenario(args.scenario), args.defense)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2) + '\n', encoding='utf8')
        print(f'Wrote trace(s) to {path}')
    print('SCENARIO                      DEFENSE  ATTACK_SUCCESS  UNAUTH_EXEC  TASK_COMPLETE  FALSE_BLOCKS')
    for r in output['results'] if args.command == 'matrix' else [output]:
        m = r['metrics']
        print(f"{r['scenario_id']:<29} {r['defense']:<8} {str(m['attack_success']):<15} {m['unauthorized_executions']:<12} {str(m['legitimate_task_complete']):<14} {m['false_blocks']}")
    if not args.out:
        print('Full machine-readable traces: add --out artifacts/results.json')


if __name__ == '__main__':
    main()
