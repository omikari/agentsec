"""Loopback-only experiment UI. Start with python -m agentsec.ui."""
from __future__ import annotations

import argparse
import importlib.util
import json
import secrets
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core import load_scenario, run_scenario

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).parent / "web"


def real_ready():
    modules = ("agentsec.agent_loop", "agentsec.model_adapter", "agentsec.scoring")
    return all(importlib.util.find_spec(name) is not None for name in modules) and (ROOT / "scenarios/demo/rubric.json").is_file()


def scenarios(mode):
    folder = ROOT / ("scenarios/demo" if mode == "real" else "scenarios")
    choices = []
    for path in sorted(folder.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            key = "scenario_id" if mode == "real" else "id"
            if key not in data or "task" not in data:
                continue
            choices.append({"file": path.name, "id": data[key], "task": data["task"],
                            "injected": bool(data.get("untrusted_annotation", "").strip()) if mode == "real"
                            else bool(data.get("attacker_text", "").strip())})
        except (ValueError, OSError):
            continue
    return choices


def execute(payload):
    mode = payload.get("mode")
    defense = payload.get("defense")
    if mode not in ("mock", "real") or defense not in ("off", "gate", "compare"):
        raise ValueError("Choose a valid mode and defense setting.")
    if mode == "real" and not real_ready():
        raise ValueError("Integrate the model adapter, agent loop, scorer and demo scenarios first.")
    selected = next((s for s in scenarios(mode) if s["file"] == payload.get("scenario")), None)
    if selected is None:
        raise ValueError("Choose an available scenario.")
    path = ROOT / ("scenarios/demo" if mode == "real" else "scenarios") / selected["file"]
    data = json.loads(path.read_text(encoding="utf-8"))
    modes = ("off", "gate") if defense == "compare" else (defense,)
    results = []
    if mode == "real":
        from .agent_loop import run_agent
        from .model_adapter import ModelAdapter
        from .scoring import score_run
        adapter = ModelAdapter.from_env()
        rubric = json.loads((ROOT / "scenarios/demo/rubric.json").read_text(encoding="utf-8"))
    for setting in modes:
        if mode == "mock":
            result = run_scenario(data, setting)
            result.update({"status": "completed", "mock": True})
        else:
            result = run_agent(data, setting, adapter, max_steps=6, timeout_s=300)
            result["scores"] = score_run(result, rubric)
        results.append(result)
    return {"id": uuid.uuid4().hex, "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": mode, "scenario": selected["id"], "results": results}


def serve(port=8765):
    token = secrets.token_urlsafe(32)
    output = ROOT / "artifacts/ui"
    jobs = {}
    lock = threading.Lock()
    executor = ThreadPoolExecutor(max_workers=1)
    active = threading.Semaphore(1)

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, data, content_type="application/json"):
            encoded = json.dumps(data).encode() if content_type == "application/json" else data
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(encoded)

        def local_host(self):
            return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def do_GET(self):
            if not self.local_host():
                return self.respond(403, {"error": "Local access only."})
            path = self.path.split("?")[0]
            if path == "/api/config":
                return self.respond(200, {"token": token, "real_ready": real_ready(),
                    "scenarios": {"mock": scenarios("mock"), "real": scenarios("real")},
                    "real_model": __import__("os").environ.get("AGENTSEC_MODEL", "")})
            if path == "/api/history":
                records = []
                for file in sorted(output.glob("*.json"), reverse=True)[:50]:
                    try:
                        records.append(json.loads(file.read_text(encoding="utf-8")))
                    except (ValueError, OSError):
                        pass
                return self.respond(200, records)
            if path.startswith("/api/jobs/"):
                with lock:
                    job = jobs.get(path.rsplit("/", 1)[-1])
                    return self.respond(200 if job else 404, job or {"error": "Unknown run."})
            allowed = {"/": ("index.html", "text/html; charset=utf-8"),
                       "/style.css": ("style.css", "text/css; charset=utf-8"),
                       "/app.js": ("app.js", "application/javascript; charset=utf-8")}
            if path not in allowed:
                return self.respond(404, {"error": "Not found."})
            name, mime = allowed[path]
            self.respond(200, (STATIC / name).read_bytes(), mime)

        def do_POST(self):
            origin = self.headers.get("Origin")
            if not self.local_host() or self.headers.get("X-AgentSec-Token") != token or (
                origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}")
            ):
                return self.respond(403, {"error": "Invalid local request."})
            if self.path != "/api/run":
                return self.respond(404, {"error": "Not found."})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 1 or size > 8192:
                    raise ValueError("Invalid request length.")
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise ValueError("Expected a configuration object.")
            except (ValueError, TypeError) as exc:
                return self.respond(400, {"error": str(exc)})
            if not active.acquire(blocking=False):
                return self.respond(409, {"error": "An experiment is already running."})
            job_id = uuid.uuid4().hex
            with lock:
                jobs[job_id] = {"status": "running"}

            def work():
                try:
                    record = execute(payload)
                    output.mkdir(parents=True, exist_ok=True)
                    filename = record["created_at"].replace(":", "-") + "_" + record["id"] + ".json"
                    record["saved_file"] = "artifacts/ui/" + filename
                    (output / filename).write_text(json.dumps(record, indent=2), encoding="utf-8")
                    outcome = {"status": "done", "record": record}
                except Exception as exc:
                    outcome = {"status": "error", "error": str(exc)}
                finally:
                    active.release()
                with lock:
                    jobs[job_id] = outcome
            executor.submit(work)
            self.respond(202, {"job_id": job_id})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"AgentSec local UI: http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        executor.shutdown(wait=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentSec local experiment interface")
    parser.add_argument("--port", type=int, default=8765)
    serve(parser.parse_args().port)
