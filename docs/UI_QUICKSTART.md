# AgentSec local UI

From the repository root:

```powershell
python -m agentsec.ui
```

Open http://127.0.0.1:8765 in your browser. Stop the server with Ctrl+C.
There are no new package dependencies. Change the port with --port 8766.

## First experiment

1. Keep Mock infrastructure test selected.
2. Select the injected scenario and Compare both.
3. Run the experiment and inspect the two results and action trace.
4. Export JSON or reopen a result in Run archive.

Mock task completion means a simulated summary action executed, not that a
real triage answer passed a rubric. Mock results are labeled throughout.

Results persist under artifacts/ui/ (ignored by Git). The UI launches only
one experiment at a time and binds to loopback. Do not expose it as a public
service or put a reverse proxy in front of it.

## Real-model integration

The UI enables real-model mode when agent_loop.py, model_adapter.py,
scoring.py, and scenarios/demo/rubric.json exist. The scenario list includes
files with scenario_id and task, excluding answer keys. Configure the model
using the environment variables documented in MODEL_SETUP.md before launch.
The UI uses ModelAdapter.from_env(), run_agent(), and score_run() directly.

Model endpoint configuration and credentials remain server-side. This UI
does not download a model, repair adapter issues, or fall back to mock if a
real run fails. Review and integrate the model-adapter PR before live use.

Zach can retain ownership of result/report refinements and fresh-clone
verification. This interface adds a local browser route without modifying
the existing CLI entry point or team-owned modules.

## Validation

```powershell
python -m unittest discover -s tests -v
```
