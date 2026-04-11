"""
inference.py — Email Operations Center OpenEnv v2 baseline inference.
Follows OpenEnv hackathon guidelines exactly:
  [START] task=<task> env=<env> model=<model>
  [STEP]  step=<n> action=<a> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
"""
#from __future___ import annotations
import os, sys, json, time, requests
from typing import Any, Dict, List, Optional
from openai import OpenAI

# ── Environment variables ──────────────────────────────────────────────────────
API_BASE_URL     = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME       = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "https://niloy456-email-ops-env.hf.space")
ENV_NAME     = "email-ops-env"
SEED         = 2024
TASKS        = ["task_easy", "task_medium", "task_hard"]
MIN_SCORE    = 0.01
MAX_SCORE    = 0.99


def clamp(x: float) -> float:
    return round(max(MIN_SCORE, min(MAX_SCORE, float(x))), 2)


# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL) if HF_TOKEN else None


# ── Env Client ────────────────────────────────────────────────────────────────
def env_reset(task_id: str, seed: int = SEED) -> Dict:
    r = requests.post(f"{ENV_BASE_URL}/reset",
                      json={"task_id": task_id, "seed": seed}, timeout=30)
    r.raise_for_status()
    return r.json()


def env_step(action: Dict) -> Dict:
    r = requests.post(f"{ENV_BASE_URL}/step", json=action, timeout=30)
    r.raise_for_status()
    return r.json()


def env_grade() -> Dict:
    r = requests.get(f"{ENV_BASE_URL}/grade", timeout=15)
    r.raise_for_status()
    return r.json()


# ── Structured logging — EXACT guideline format ───────────────────────────────
def log_start(task_id: str) -> None:
    print(f"[START] task={task_id} env={ENV_NAME} model={MODEL_NAME}", flush=True)


def log_step(step_n: int, action: str, reward: float,
             done: bool, error: Optional[str] = None) -> None:
    print(
        f"[STEP] step={step_n} action={action} "
        f"reward={reward:.2f} done={'true' if done else 'false'} "
        f"error={error if error else 'null'}",
        flush=True
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={'true' if success else 'false'} "
        f"steps={steps} rewards={rewards_str}",
        flush=True
    )


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert email operations agent.

WORKFLOW: select_email -> extract_intent -> lookup tool -> route/reply/escalate/delete

DEPARTMENTS: support, billing, legal, engineering, sales, hr, compliance, executive
URGENCY: critical, high, medium, low

RULES:
- SPAM/phishing -> DELETE
- must_escalate policy -> ESCALATE
- no_auto_reply policy -> route, not reply
- VIP or financial > $10k -> HIGH urgency minimum

RESPOND ONLY WITH VALID JSON. Examples:
{"action_type": "select_email"}
{"action_type": "extract_intent", "intent": "outage_report", "urgency": "critical"}
{"action_type": "lookup_ticket", "lookup_id": "TKT-4421"}
{"action_type": "route", "route_to": "engineering", "urgency": "critical"}
{"action_type": "reply", "reply_text": "Dear customer, we are investigating..."}
{"action_type": "escalate", "reason": "Legal threat"}
{"action_type": "delete"}
"""


# ── LLM Agent ─────────────────────────────────────────────────────────────────
def call_llm(messages: List[Dict]) -> str:
    """All LLM calls use the OpenAI client configured via environment variables."""
    if client is None:
        raise RuntimeError("No LLM client")
    resp = client.chat.completions.create(
        model=MODEL_NAME, messages=messages,
        max_tokens=300, temperature=0.1, seed=SEED,
    )
    return resp.choices[0].message.content.strip()


def parse_action(text: str) -> Optional[Dict]:
    text = text.strip()
    if "" in text:
        for p in text.split(""):
            p = p.strip().lstrip("json").strip()
            if p.startswith("{"): text = p; break
    try:
        return json.loads(text)
    except Exception:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try: return json.loads(text[s:e])
            except Exception: pass
    return None


# ── Rule-based fallback ───────────────────────────────────────────────────────
def rule_agent(obs: Dict) -> Dict:
    current = obs.get("current_email")
    if not current:
        inbox = obs.get("inbox", [])
        if not inbox: return {"action_type": "archive"}
        best = sorted(inbox, key=lambda e: (
            e.get("sla_remaining", 99), -e.get("financial_impact", 0)))[0]
        return {"action_type": "select_email", "email_id": best["id"]}

    policy    = current.get("policy_rules", [])
    subject   = current.get("subject", "").lower()
    body      = current.get("body", "").lower()
    sender    = current.get("sender_email", "").lower()
    financial = current.get("financial_impact", 0)
    vip       = current.get("vip", False)

    if current.get("agent_intent") is None:
        intent, urgency = "general_inquiry", "medium"
        for kw, i in [("outage","outage"),("down","outage"),("breach","security_incident"),
                      ("hipaa","compliance_request"),("legal","legal_dispute"),
                      ("harassment","harassment_complaint"),("quit","resignation"),
                      ("refund","refund_request"),("billing","billing_inquiry"),
                      ("spam","spam"),("phishing","phishing")]:
            if kw in subject or kw in body: intent = i; break
        if financial > 50000 or vip or "critical" in subject: urgency = "critical"
        elif financial > 5000 or "urgent" in subject: urgency = "high"
        return {"action_type": "extract_intent", "intent": intent, "urgency": urgency}

    if not current.get("tool_was_called", False):
        import re
        for pat, tool in [(r'TKT-\d+','lookup_ticket'),(r'ORD-\d+','lookup_order'),
                          (r'C-\d{4}','lookup_customer')]:
            m = re.search(pat, body + " " + subject)
            if m: return {"action_type": tool, "lookup_id": m.group()}
        if vip or financial > 10000:
            return {"action_type": "lookup_customer", "lookup_id": sender}

    if "must_escalate" in policy:
        return {"action_type": "escalate", "reason": "Policy requires escalation"}
    if "no_auto_reply" in policy:
        dept = "legal" if ("legal" in body or "hipaa" in body) else "compliance"
        return {"action_type": "route", "route_to": dept, "urgency": "high"}

    intent = current.get("agent_intent", "")
    if intent in ("spam", "phishing"):
        return {"action_type": "delete"}

    route_map = {
        "outage":("engineering","critical"), "security_incident":("engineering","critical"),
        "legal_dispute":("legal","critical"), "harassment_complaint":("hr","critical"),
        "whistleblower_report":("legal","critical"), "data_deletion_request":("compliance","high"),
        "compliance_request":("compliance","high"), "billing_inquiry":("billing","medium"),
        "refund_request":("billing","high"), "sales_inquiry":("sales","high"),
        "churn_risk":("executive","critical"), "resignation":("hr","high"),
        "medical_leave":("hr","critical"), "compensation_complaint":("hr","high"),
    }
    if intent in route_map:
        dept, urg = route_map[intent]
        return {"action_type": "route", "route_to": dept, "urgency": urg}

    if current.get("requires_reply", False):
        return {"action_type": "reply", "reply_text": (
            f"Dear {current.get('sender','Customer')},\n\nThank you for contacting us. "
            "Our team will respond within one business day.\n\nBest regards,\nOperations Team"
        )}
    return {"action_type": "archive"}


# ── Main Run Loop ─────────────────────────────────────────────────────────────
def run_task(task_id: str, use_llm: bool) -> Dict[str, Any]:
    max_steps       = {"task_easy": 60, "task_medium": 150, "task_hard": 300}[task_id]
    rewards: List[float] = []
    messages        = [{"role": "system", "content": SYSTEM_PROMPT}]
    llm_disabled    = False
    consec_fails    = 0
    success         = False

    log_start(task_id)

    try:
        obs = env_reset(task_id, SEED)
    except Exception as e:
        log_end(success=False, steps=0, rewards=[])
        return {"task_id": task_id, "final_score": MIN_SCORE, "steps": 0}

    for step_n in range(1, max_steps + 1):
        if obs.get("done", False):
            success = True
            break

        action     = None
        step_error = None

        if use_llm and client is not None and not llm_disabled:
            try:
                messages.append({"role": "user",
                                  "content": format_obs(obs)})
                out    = call_llm(messages)
                messages.append({"role": "assistant", "content": out})
                action = parse_action(out)
                if action: consec_fails = 0
                else: consec_fails += 1
            except Exception as ex:
                consec_fails += 1
                if "402" in str(ex) or "depleted" in str(ex) or consec_fails >= 3:
                    llm_disabled = True

        if action is None:
            action = rule_agent(obs)

        try:
            result     = env_step(action)
            raw_rv     = float(result["reward"]["value"])
            rv         = clamp(raw_rv)   # clamp to (0.01, 0.99)
            obs        = result["observation"]
            done       = result.get("done", False)
            step_error = None
        except Exception as ex:
            rv         = MIN_SCORE
            step_error = str(ex)[:60]
            done       = False

        rv = clamp(rv)   # ensure each step reward is in (0.01, 0.99)
        rewards.append(rv)
        log_step(step_n, action.get("action_type", "unknown"),
                 rv, done, step_error)

        if done:
            success = True
            break

    try:
        score = clamp(env_grade().get("score", MIN_SCORE))
    except Exception:
        score = clamp(sum(rewards) / max(1, len(rewards)))

    log_end(success=success, steps=len(rewards), rewards=rewards)
    return {"task_id": task_id, "final_score": score,
            "steps": len(rewards), "success": success}


def format_obs(obs: Dict) -> str:
    lines = [f"Step {obs['step_count']} | Inbox: {len(obs.get('inbox',[]))} | "
             f"Processed: {len(obs.get('processed',[]))}"]
    cur = obs.get("current_email")
    if cur:
        lines += [f"ID: {cur['id']}", f"Subject: {cur['subject']}",
                  f"SLA: {cur.get('sla_remaining','?')} steps",
                  f"Policy: {cur.get('policy_rules',[])}",
                  f"Body:\n{cur['body'][:500]}", "\nNext action?"]
    else:
        lines.append("INBOX:")
        for e in obs.get("inbox",[])[:5]:
            lines.append(f"  [{e['id']}] SLA:{e.get('sla_remaining','?')} {e.get('subject','')[:50]}")
        lines.append("Select most urgent email.")
    return "\n".join(lines)


def main() -> None:
    try:
        requests.get(f"{ENV_BASE_URL}/health", timeout=10).raise_for_status()
    except Exception:
        log_end(success=False, steps=0, rewards=[])
        sys.exit(1)

    use_llm = client is not None
    results = {}
    for task_id in TASKS:
        try:
            results[task_id] = run_task(task_id, use_llm)
        except Exception:
            log_end(success=False, steps=0, rewards=[])
            results[task_id] = {"task_id": task_id, "final_score": MIN_SCORE, "steps": 0}

    scores = [clamp(r.get("final_score", MIN_SCORE)) for r in results.values()]
    output = {
        "run_config": {"model": MODEL_NAME, "api_base": API_BASE_URL,
                       "seed": SEED, "use_llm": use_llm},
        "scores":     {t: clamp(r.get("final_score", MIN_SCORE)) for t, r in results.items()},
        "average_score": clamp(sum(scores) / len(scores)),
        "runtime_seconds": 0,
    }
    with open("baseline_results.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    main()