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

On the integration branch, select Real model mode, enter the compatible API
base URL (for local Ollama, `http://localhost:11434/v1`), and click **Find models**.
Choose a discovered identifier or type an installed model name. **Test tool
connection** sends one bounded inference request and checks for a valid evidence
read request; it does not execute tools or download models. Discovery may be
unsupported by some endpoints; manual entry still works.

Credentials are read from `AGENTSEC_MODEL_API_KEY` on the server and are used
only for the endpoint configured in `AGENTSEC_MODEL_BASE_URL`. They cannot be
entered or exported through the browser. Connection settings currently last
for the page session; environment values supply startup defaults.

Edit the alert-feed annotation and click **Save new version** before running.
The original preset is preserved. Variants are exploratory and stored under
`artifacts/scenarios/`, which is ignored by Git. Exported runs include the full
scenario and its hash. The annotation is delivered after a successful evidence
read; the report shows delivery separately from task and security outcomes.

The November 12 integration passed offline and browser mock checks. No reachable
local Ollama server was available, so completed real-model runs remain unverified.

The UI enables real-model mode when agent_loop.py, model_adapter.py,
scoring.py, and scenarios/demo/rubric.json exist. The scenario list includes
files with scenario_id and task, excluding answer keys. Environment variables
documented in MODEL_SETUP.md provide optional startup defaults.
The UI builds ModelConfig from the selected endpoint/model and server environment,
then uses ModelAdapter, run_agent(), and score_run() directly.

Credentials remain server-side. Endpoint and model identifiers are visible in the UI and run records. This UI
does not download a model, repair adapter issues, or fall back to mock if a
real run fails. Review and integrate the model-adapter PR before live use.

Zach can retain ownership of result/report refinements and fresh-clone
verification. This interface adds a local browser route without modifying
the existing CLI entry point or team-owned modules.

## Validation

```powershell
python -m unittest discover -s tests -v
```
