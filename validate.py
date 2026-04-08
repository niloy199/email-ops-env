"""
validate.py — Pre-submission validator for Email Ops OpenEnv v2
"""
from __future__ import annotations
import sys, argparse, requests

P = "✓ PASS"; F = "✗ FAIL"

def check(label, ok, detail=""):
    print(f"  {P if ok else F} | {label}" + (f" — {detail}" if detail else ""))
    return ok

def section(t):
    print(f"\n{'─'*60}\n  {t}\n{'─'*60}")

def run_quick_episode(env_url, task_id):
    requests.post(f"{env_url}/reset", json={"task_id": task_id, "seed": 42})
    for _ in range(80):
        s = requests.get(f"{env_url}/state", timeout=10).json()
        if s.get("done"): break
        cur = s.get("current_email")
        if cur is None:
            inbox = s.get("inbox", [])
            if not inbox: break
            action = {"action_type": "select_email", "email_id": inbox[0]["id"]}
        else:
            if not cur.get("agent_intent"):
                action = {"action_type": "extract_intent", "intent": "general_inquiry", "urgency": "medium"}
            elif cur.get("policy_rules"):
                action = {"action_type": "escalate", "reason": "Policy requires review"}
            else:
                action = {"action_type": "route", "route_to": "support", "urgency": "medium"}
        r = requests.post(f"{env_url}/step", json=action, timeout=10).json()
        if r.get("done"): break
    return requests.get(f"{env_url}/grade", timeout=10).json().get("score", 0.01)

def validate(env_url):
    ok_all = True
    print("="*60)
    print("  Email Ops OpenEnv v2 — Validator")
    print("="*60)
    print(f"  Target: {env_url}")

    section("1. Health Check")
    try:
        r = requests.get(f"{env_url}/health", timeout=10)
        ok_all &= check("GET /health returns 200", r.status_code == 200 and r.json().get("status") == "ok", f"status={r.status_code}")
    except Exception as e:
        ok_all &= check("GET /health", False, str(e))

    section("2. OpenEnv Spec: reset()")
    for tid in ["task_easy", "task_medium", "task_hard"]:
        try:
            r = requests.post(f"{env_url}/reset", json={"task_id": tid, "seed": 42}, timeout=15)
            d = r.json()
            ok = r.status_code == 200 and all(k in d for k in ["inbox","done","step_count","inbox_size","scenario","sla_breached"])
            ok_all &= check(f"reset({tid})", ok, f"inbox={len(d.get('inbox',[]))} emails")
        except Exception as e:
            ok_all &= check(f"reset({tid})", False, str(e))

    section("3. OpenEnv Spec: state()")
    try:
        r = requests.get(f"{env_url}/state", timeout=10)
        d = r.json()
        required = ["inbox","processed","step_count","done","inbox_size","task_id","tool_results","sla_breached","pending_arrivals","scenario"]
        missing = [f for f in required if f not in d]
        ok_all &= check("GET /state typed Observation", not missing, f"missing={missing}" if missing else "all fields present")
    except Exception as e:
        ok_all &= check("GET /state", False, str(e))

    section("4. OpenEnv Spec: step()")
    requests.post(f"{env_url}/reset", json={"task_id": "task_easy", "seed": 42})
    try:
        r = requests.post(f"{env_url}/step", json={"action_type": "select_email"}, timeout=10)
        d = r.json()
        ok = r.status_code == 200 and all(k in d for k in ["observation","reward","done","info"])
        rv = d.get("reward", {}).get("value")
        ok_all &= check("step() returns (obs, reward, done, info)", ok)
        ok_all &= check("reward.value in [-1.0, 1.0]", rv is not None and -1.0 <= rv <= 1.0, f"reward={rv}")
    except Exception as e:
        ok_all &= check("step()", False, str(e))

    section("5. Task Graders (3 tasks, scores 0.0–1.0)")
    for tid in ["task_easy", "task_medium", "task_hard"]:
        try:
            requests.post(f"{env_url}/reset", json={"task_id": tid, "seed": 42})
            score = run_quick_episode(env_url, tid)
            ok_all &= check(f"Grader {tid}: score in [0.0, 1.0]", 0.0 < score < 1.0, f"score={score:.4f}")
        except Exception as e:
            ok_all &= check(f"Grader {tid}", False, str(e))

    section("6. openenv.yaml Compliance")
    try:
        r = requests.get(f"{env_url}/validate", timeout=20)
        d = r.json()
        ok_all &= check("openenv.yaml valid", d.get("valid", False), d.get("message", ""))
        for k, v in d.get("checks", {}).items():
            if isinstance(v, dict) and "ok" in v:
                check(f"  ↳ {k}", v["ok"], str(v.get("error", "")))
    except Exception as e:
        ok_all &= check("openenv.yaml", False, str(e))

    section("7. Tasks Enumeration")
    try:
        r = requests.get(f"{env_url}/tasks", timeout=10)
        tasks = r.json().get("tasks", [])
        ok_all &= check("GET /tasks returns ≥ 3 tasks", len(tasks) >= 3, f"found {len(tasks)}")
        for t in tasks:
            check(f"  ↳ {t['id']} ({t['difficulty']})", True, t["description"][:60])
    except Exception as e:
        ok_all &= check("GET /tasks", False, str(e))

    section("8. Tools Endpoint")
    try:
        r = requests.get(f"{env_url}/tools", timeout=10)
        tools = r.json().get("tools", [])
        ok_all &= check("GET /tools returns tool list", r.status_code == 200 and len(tools) >= 3, f"found {len(tools)} tools")
    except Exception as e:
        ok_all &= check("GET /tools", False, str(e))

    print(f"\n{'='*60}")
    print(f"  {'✓ ALL CHECKS PASSED — Ready to submit!' if ok_all else '✗ SOME CHECKS FAILED'}")
    print(f"{'='*60}\n")
    return ok_all

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-url", default="http://localhost:7860")
    args = parser.parse_args()
    sys.exit(0 if validate(args.env_url) else 1)
