"""
FastAPI server — Email Operations Center OpenEnv v2
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import yaml

from env.environment import EmailOpsEnv
from env.models import Action, Observation, ResetRequest, StepResponse
from graders.graders import grade_episode

MIN_SCORE = 0.01
MAX_SCORE = 0.99

app = FastAPI(
    title="Email Operations Center OpenEnv",
    description="Agentic email environment with SLA, tool use, policy constraints, and dynamic inbox.",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

env = EmailOpsEnv()


@app.get("/", response_class=HTMLResponse)
async def root():
    return """<!DOCTYPE html><html><head><title>Email Ops OpenEnv v2</title>
    <style>body{font-family:system-ui,sans-serif;max-width:860px;margin:60px auto;padding:0 20px;background:#0d1117;color:#e6edf3}
    h1{color:#58a6ff}h2{color:#7ee787}code{background:#161b22;padding:2px 6px;border-radius:4px;color:#f0883e}
    .ep{background:#161b22;border-left:3px solid #58a6ff;padding:10px 16px;margin:8px 0;border-radius:4px}
    a{color:#58a6ff}.b{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;margin-left:8px}
    .post{background:#388bfd33;color:#58a6ff}.get{background:#3fb95033;color:#7ee787}
    .badge{background:#53341133;color:#f0883e;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px}</style>
    </head><body>
    <h1>📧 Email Operations Center — OpenEnv v2</h1>
    <p>Agentic environment: chain-of-thought reasoning, tool use (CRM/tickets/orders),
    SLA timers, policy constraints, dynamic inbox, 4 scenario types.</p>
    <h2>Chain-of-thought workflow</h2>
    <p>select_email → extract_intent → lookup_customer/ticket/order → route/reply/escalate</p>
    <h2>Endpoints</h2>
    <div class="ep"><span class="b post">POST</span> <code>/reset</code> — Start new episode</div>
    <div class="ep"><span class="b post">POST</span> <code>/step</code> — Execute action</div>
    <div class="ep"><span class="b get">GET</span> <code>/state</code> — Current state</div>
    <div class="ep"><span class="b get">GET</span> <code>/tasks</code> — List tasks</div>
    <div class="ep"><span class="b get">GET</span> <code>/tools</code> — Available tools</div>
    <div class="ep"><span class="b get">GET</span> <code>/grade</code> — Grade episode</div>
    <div class="ep"><span class="b get">GET</span> <code>/validate</code> — OpenEnv compliance</div>
    <div class="ep"><span class="b get">GET</span> <code>/health</code> — Health check</div>
    <h2>Tasks</h2>
    <p><span class="badge">easy</span> task_easy — Startup support, 8 emails</p>
    <p><span class="badge">medium</span> task_medium — HR inbox, 15 emails, SLA + policy</p>
    <p><span class="badge">hard</span> task_hard — Healthcare admin, 25 emails, adversarial + HIPAA</p>
    <p><a href="/docs">📖 Swagger UI</a></p></body></html>"""


@app.get("/health")
async def health():
    return {"status": "ok", "service": "email-ops-openenv", "version": "2.0.0"}


@app.post("/reset", response_model=Observation)
async def reset(request: ResetRequest = None):
    if request is None:
        request = ResetRequest()
    try:
        return env.reset(task_id=request.task_id, seed=request.seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResponse)
async def step(action: Action):
    return env.step(action)


@app.get("/state", response_model=Observation)
async def state():
    return env.state()


@app.get("/tasks")
async def list_tasks():
    tasks = env.get_tasks()
    return {"tasks": [t.model_dump() for t in tasks]}


@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "action_type": "lookup_customer",
                "description": "Query CRM by customer ID or email",
                "fields": {"lookup_id": "customer ID (e.g. C-1001) or email address"},
            },
            {
                "action_type": "lookup_ticket",
                "description": "Query ticket DB by ticket ID or customer ID",
                "fields": {"lookup_id": "ticket ID (e.g. TKT-4421) or customer ID"},
            },
            {
                "action_type": "lookup_order",
                "description": "Query order system by order ID or customer ID",
                "fields": {"lookup_id": "order ID (e.g. ORD-9001) or customer ID"},
            },
        ]
    }


@app.get("/grade")
async def grade():
    s = env.state()
    raw_score, details = grade_episode(s.task_id or "task_easy", s.processed)
    score = max(MIN_SCORE, min(MAX_SCORE, float(raw_score)))
    return {
        "task_id": s.task_id,
        "score": score,
        "done": s.done,
        "emails_processed": len(s.processed),
        "details": details,
    }


@app.get("/validate")
async def validate():
    results = {}

    try:
        obs = env.reset(task_id="task_easy", seed=42)
        results["reset"] = {"ok": True, "inbox_size": len(obs.inbox)}
    except Exception as e:
        results["reset"] = {"ok": False, "error": str(e)}

    try:
        s = env.state()
        required = ["inbox", "processed", "step_count", "done", "inbox_size", "task_id",
                    "tool_results", "sla_breached", "pending_arrivals", "scenario"]
        missing = [f for f in required if not hasattr(s, f)]
        results["state"] = {"ok": not missing, "missing": missing}
    except Exception as e:
        results["state"] = {"ok": False, "error": str(e)}

    try:
        from env.models import Action, ActionType
        r = env.step(Action(action_type=ActionType.SELECT_EMAIL))
        results["step"] = {"ok": True, "reward": r.reward.value, "done": r.done}
    except Exception as e:
        results["step"] = {"ok": False, "error": str(e)}

    grader_results = {}
    for tid in ["task_easy", "task_medium", "task_hard"]:
        try:
            env.reset(task_id=tid, seed=42)
            score, _ = grade_episode(tid, [])
            grader_results[tid] = {"ok": True, "empty_score": score}
        except Exception as e:
            grader_results[tid] = {"ok": False, "error": str(e)}
    results["graders"] = grader_results

    try:
        yaml_path = os.path.join(ROOT, "openenv.yaml")
        with open(yaml_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        results["openenv_yaml"] = {
            "ok": True,
            "name": spec.get("name"),
            "tasks": len(spec.get("tasks", [])),
        }
    except Exception as e:
        results["openenv_yaml"] = {"ok": False, "error": str(e)}

    def is_ok(v):
        if isinstance(v, dict) and "ok" in v:
            return v["ok"]
        if isinstance(v, dict):
            return all(is_ok(x) for x in v.values())
        return False

    all_ok = all(is_ok(v) for v in results.values())
    return {
        "valid": all_ok,
        "checks": results,
        "message": "All checks passed" if all_ok else "Some checks failed",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
