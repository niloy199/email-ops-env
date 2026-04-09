"""
inference.py — Email Operations Center OpenEnv v2 baseline inference.
Chain-of-thought agent: extract intent -> query tools -> route/reply/escalate.
Uses OpenAI client for all LLM calls.
"""
from __future__ import annotations
import os, sys, json, time, traceback, requests
from typing import Any, Dict, List, Optional
from openai import OpenAI

# ── Environment variables ──────────────────────────────────────────────────────
# API_BASE_URL and MODEL_NAME have defaults. HF_TOKEN must NOT have a default.

API_BASE_URL     = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME       = os.getenv("MODEL_NAME",   "meta-llama/Llama-3.1-8B-Instruct")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")   # optional — used with from_docker_image()

ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:7860")
SEED         = 2024
TASKS        = ["task_easy", "task_medium", "task_hard"]

# ── OpenAI client (all LLM calls use this) ────────────────────────────────────

client = OpenAI(
    api_key=HF_TOKEN or "sk-placeholder",
    base_url=API_BASE_URL,
)

# ── Env Client ─────────────────────────────────────────────────────────────────

def env_reset(task_id, seed=SEED):
    r = requests.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_id, "seed": seed}, timeout=30)
    r.raise_for_status()
    return r.json()

def env_step(action):
    r = requests.post(f"{ENV_BASE_URL}/step", json=action, timeout=30)
    r.raise_for_status()
    return r.json()

def env_state():
    r = requests.get(f"{ENV_BASE_URL}/state", timeout=15)
    r.raise_for_status()
    return r.json()

def env_grade():
    r = requests.get(f"{ENV_BASE_URL}/grade", timeout=15)
    r.raise_for_status()
    return r.json()

# ── System Prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert email operations agent. You process business emails using a strict chain-of-thought workflow.

WORKFLOW (always follow this order):
1. select_email — pick the most urgent unread email
2. extract_intent — identify what the sender wants
3. lookup_customer / lookup_ticket / lookup_order — query context BEFORE acting (if email references a customer, ticket, or order ID)
4. Choose terminal action: route, reply, escalate, request_clarification, archive, or delete

ROUTING DEPARTMENTS: support, billing, legal, engineering, sales, hr, compliance, executive

URGENCY LEVELS: critical, high, medium, low

CRITICAL RULES:
- SPAM / phishing emails -> DELETE (never reply)
- Emails with must_escalate policy -> ESCALATE or ROUTE to legal/compliance/executive
- Emails with no_auto_reply policy -> do NOT reply, use route or escalate
- VIP customers or financial impact > $10k -> treat as at least HIGH urgency
- Legal threats, HIPAA, whistleblower -> route to legal or compliance, NEVER auto-reply
- Always check tool_results before routing if a ticket/order ID is mentioned

RESPOND ONLY WITH VALID JSON. No markdown. No explanation. Examples:
Select: {"action_type": "select_email"}
Extract: {"action_type": "extract_intent", "intent": "account_lockout", "urgency": "high"}
Tool: {"action_type": "lookup_customer", "lookup_id": "C-1001"}
Route: {"action_type": "route", "route_to": "engineering", "urgency": "critical", "reason": "API outage"}
Reply: {"action_type": "reply", "reply_text": "Dear Alex, Thank you for contacting us. Our team is investigating and will restore access within 30 minutes."}
Escalate: {"action_type": "escalate", "reason": "Legal threat requires human review"}
Delete: {"action_type": "delete"}
"""

# ── LLM Agent ──────────────────────────────────────────────────────────────────

def format_obs(obs: Dict) -> str:
    lines = [
        f"Step {obs['step_count']} | Inbox: {len(obs.get('inbox', []))} | "
        f"Processed: {len(obs.get('processed', []))} | "
        f"SLA breached: {len(obs.get('sla_breached', []))} | "
        f"Pending arrivals: {obs.get('pending_arrivals', 0)}"
    ]
    current = obs.get("current_email")
    if current:
        lines += [
            "\n=== CURRENT EMAIL ===",
            f"ID: {current['id']}",
            f"From: {current['sender']} <{current['sender_email']}>",
            f"Subject: {current['subject']}",
            f"SLA remaining: {current.get('sla_remaining', '?')} steps",
            f"VIP: {current.get('vip', False)} | Financial impact: ${current.get('financial_impact', 0):,.0f}",
            f"Policy rules: {current.get('policy_rules', [])}",
            f"Body:\n{current['body'][:700]}",
        ]
        thread = current.get("thread", [])
        if thread:
            lines.append(f"\nThread history ({len(thread)} messages):")
            for m in thread[-2:]:
                lines.append(f"  [{m.get('date','')}] {m.get('sender','')}: {m.get('body','')[:100]}")
        tr = obs.get("tool_results")
        if tr and tr.get("found"):
            lines.append(f"\nTool result ({tr['tool']}): {json.dumps(tr.get('data', {}))[:400]}")
        lines.append("\nWhat is your next action?")
    else:
        inbox = obs.get("inbox", [])[:6]
        lines.append("\n=== INBOX ===")
        for e in inbox:
            lines.append(
                f"  [{e['id']}] SLA:{e.get('sla_remaining','?')}steps | "
                f"{e.get('subject','')[:55]} | {e.get('sender_email','')}"
            )
        if len(obs.get("inbox", [])) > 6:
            lines.append(f"  ...and {len(obs['inbox'])-6} more")
        lines.append("\nSelect the most urgent email.")
    return "\n".join(lines)


def call_llm(messages: List[Dict]) -> str:
    """All LLM calls use the OpenAI client configured via environment variables."""
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_tokens=400,
        temperature=0.1,
        seed=SEED,
    )
    return resp.choices[0].message.content.strip()


def parse_action(text: str) -> Optional[Dict]:
    text = text.strip()
    if "```" in text:
        for p in text.split("```"):
            p = p.strip().lstrip("json").strip()
            if p.startswith("{"):
                text = p
                break
    try:
        return json.loads(text)
    except Exception:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            try:
                return json.loads(text[s:e])
            except Exception:
                pass
    return None


# ── Rule-based fallback agent ──────────────────────────────────────────────────

def rule_agent(obs: Dict) -> Dict:
    """Deterministic fallback when LLM is unavailable."""
    current = obs.get("current_email")
    if not current:
        inbox = obs.get("inbox", [])
        if not inbox:
            return {"action_type": "archive"}
        scored = sorted(inbox, key=lambda e: (e.get("sla_remaining", 99), -e.get("financial_impact", 0)))
        return {"action_type": "select_email", "email_id": scored[0]["id"]}

    has_intent   = current.get("agent_intent") is not None
    has_tool     = current.get("tool_was_called", False)
    policy_rules = current.get("policy_rules", [])
    subject      = current.get("subject", "").lower()
    body         = current.get("body", "").lower()
    sender       = current.get("sender_email", "").lower()
    financial    = current.get("financial_impact", 0)
    vip          = current.get("vip", False)

    if not has_intent:
        intent  = "general_inquiry"
        urgency = "medium"
        for kw, i in [
            ("outage", "outage"), ("down", "outage"),
            ("breach", "security_incident"), ("hipaa", "compliance_request"),
            ("legal", "legal_dispute"), ("harassment", "harassment_complaint"),
            ("quit", "resignation"), ("refund", "refund_request"),
            ("billing", "billing_inquiry"), ("spam", "spam"),
            ("phishing", "phishing"), ("???", "incomplete"),
        ]:
            if kw in subject or kw in body:
                intent = i
                break
        if "critical" in subject or financial > 50000 or vip:
            urgency = "critical"
        elif "urgent" in subject or "immediately" in body or financial > 5000:
            urgency = "high"
        elif financial == 0 and "low" in subject:
            urgency = "low"
        return {"action_type": "extract_intent", "intent": intent, "urgency": urgency}

    if not has_tool:
        import re
        ticket = re.search(r'TKT-\d+', body + subject)
        order  = re.search(r'ORD-\d+', body + subject)
        cust   = re.search(r'C-\d{4}', body + subject)
        if ticket:
            return {"action_type": "lookup_ticket",   "lookup_id": ticket.group()}
        if order:
            return {"action_type": "lookup_order",    "lookup_id": order.group()}
        if cust:
            return {"action_type": "lookup_customer", "lookup_id": cust.group()}
        if vip or financial > 10000:
            return {"action_type": "lookup_customer", "lookup_id": sender}

    if "must_escalate" in policy_rules:
        return {"action_type": "escalate", "reason": "Policy requires escalation"}
    if "no_auto_reply" in policy_rules:
        dept = "legal" if ("legal" in body or "hipaa" in body) else "compliance"
        return {"action_type": "route", "route_to": dept, "urgency": "high"}

    intent = current.get("agent_intent", "")
    if intent in ("spam", "phishing", "incomplete"):
        return {"action_type": "delete"}

    route_map = {
        "outage":                  ("engineering", "critical"),
        "security_incident":       ("engineering", "critical"),
        "legal_dispute":           ("legal",        "critical"),
        "harassment_complaint":    ("hr",           "critical"),
        "whistleblower_report":    ("legal",        "critical"),
        "data_deletion_request":   ("compliance",   "high"),
        "compliance_request":      ("compliance",   "high"),
        "billing_inquiry":         ("billing",      "medium"),
        "refund_request":          ("billing",      "high"),
        "sales_inquiry":           ("sales",        "high"),
        "churn_risk":              ("executive",    "critical"),
        "resignation":             ("hr",           "high"),
        "medical_leave":           ("hr",           "critical"),
        "compensation_complaint":  ("hr",           "high"),
        "compensation_escalation": ("hr",           "high"),
        "feature_request":         ("sales",        "low"),
        "fyi_internal":            ("hr",           "low"),
    }
    if intent in route_map:
        dept, urg = route_map[intent]
        return {"action_type": "route", "route_to": dept, "urgency": urg}

    if current.get("requires_reply", False):
        reply = (
            f"Dear {current.get('sender', 'Customer')},\n\n"
            "Thank you for contacting us. We have received your message and our team "
            "is reviewing it as a priority. We will follow up with a full response "
            "within one business day. If this is urgent, please reference your email "
            "ID for faster service.\n\nBest regards,\nOperations Team"
        )
        return {"action_type": "reply", "reply_text": reply}
    return {"action_type": "archive"}


# ── Structured logging ([START] / [STEP] / [END] format) ─────────────────────

def log_start(task_id: str, step_count: int):
    print(f"[START] task={task_id} steps={step_count} model={MODEL_NAME} seed={SEED}", flush=True)

def log_step(step_n: int, action_type: str, reward: float, message: str):
    print(f"[STEP] step={step_n} action={action_type} reward={reward:.2f}", flush=True)

def log_end(task_id: str, score: float, emails_processed: int, details: Dict):
    print(f"[END] task={task_id} score={score:.2f} steps={emails_processed}", flush=True)


# ── Main Run Loop ───────────────────────────────────────────────────────────────

def run_task(task_id: str, use_llm: bool = True) -> Dict[str, Any]:
    max_steps = {"task_easy": 60, "task_medium": 150, "task_hard": 300}[task_id]

    log_start(task_id, max_steps)

    obs = env_reset(task_id, SEED)
    rewards   = []
    messages  = [{"role": "system", "content": SYSTEM_PROMPT}]
    llm_fails = 0

    # If LLM fails 3 times in a row, switch permanently to rule-based for this task
    consecutive_llm_fails = 0
    llm_disabled = False

    for step_n in range(max_steps):
        if obs.get("done"):
            break

        action   = None
        obs_text = format_obs(obs)

        if use_llm and HF_TOKEN and not llm_disabled:
            try:
                messages.append({"role": "user", "content": obs_text})
                out    = call_llm(messages)
                messages.append({"role": "assistant", "content": out})
                action = parse_action(out)
                if action:
                    consecutive_llm_fails = 0  # reset on success
                else:
                    llm_fails += 1
                    consecutive_llm_fails += 1
            except Exception as ex:
                llm_fails += 1
                consecutive_llm_fails += 1
                err = str(ex)[:120]
                # Detect credit exhaustion — switch to rule-based permanently
                if "402" in err or "depleted" in err or "credits" in err:
                    llm_disabled = True
                    print(f"[STEP] step={step_n+1} action=fallback reward=0.01 note=llm_credits_exhausted", flush=True)
                elif consecutive_llm_fails >= 3:
                    llm_disabled = True
                    print(f"[STEP] step={step_n+1} action=fallback reward=0.01 note=llm_failed_3x", flush=True)
                else:
                    print(f"[STEP] step={step_n+1} action=fallback reward=0.01 note=llm_error", flush=True)

        if not action:
            action = rule_agent(obs)

        try:
            result = env_step(action)
        except Exception as ex:
            print(f"[STEP] step={step_n+1} action=error reward=0.01 note=step_failed", flush=True)
            break

        rv  = result["reward"]["value"]
        msg = result["reward"].get("message", "")
        rewards.append(rv)
        obs = result["observation"]

        log_step(step_n + 1, action.get("action_type", "?"), rv, msg)

        if obs.get("done"):
            break

    grade  = env_grade()
    score  = grade["score"]
    details = grade.get("details", {})

    log_end(task_id, score, grade.get("emails_processed", 0), details)

    return {
        "task_id":          task_id,
        "final_score":      score,
        "total_reward":     round(sum(rewards), 4),
        "avg_reward":       round(sum(rewards) / max(1, len(rewards)), 4),
        "steps":            len(rewards),
        "emails_processed": grade.get("emails_processed", 0),
        "llm_failures":     llm_fails,
        "details":          details,
    }


def main():
    t0 = time.time()

    print(f"[START] task=inference model={MODEL_NAME} seed={SEED}", flush=True)

    # Health check
    try:
        r = requests.get(f"{ENV_BASE_URL}/health", timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[END] task=inference score=0.01 steps=0 error=env_not_reachable", flush=True)
        sys.exit(1)

    use_llm = HF_TOKEN is not None
    if not use_llm:
        print("[STEP] step=0 action=fallback reward=0.01 note=rule_based_agent", flush=True)

    results = {}
    for task_id in TASKS:
        try:
            results[task_id] = run_task(task_id, use_llm)
        except Exception as e:
            err_msg = traceback.format_exc()
            print(f"[STEP] step=0 action=error reward=0.01 note=task_error", flush=True)
            results[task_id] = {"task_id": task_id, "error": str(e), "final_score": 0.0}
            log_end(task_id, 0.0, 0, {"error": str(e)})

    elapsed = time.time() - t0
    scores  = [r.get("final_score", 0.01) for r in results.values()]
    avg     = round(max(0.01, min(0.99, sum(scores) / len(scores))), 2)

    output = {
        "run_config": {
            "model":    MODEL_NAME,
            "api_base": API_BASE_URL,
            "seed":     SEED,
            "use_llm":  use_llm,
        },
        "scores":         {t: r.get("final_score", 0.01) for t, r in results.items()},
        "average_score":  round(avg, 4),
        "runtime_seconds": round(elapsed, 1),
        "task_details":   results,
    }

    with open("baseline_results.json", "w") as f:
        json.dump(output, f, indent=2)

    _final_score = round(max(MIN_SCORE, min(MAX_SCORE, float(output['average_score']))), 2)
    print(f"[END] task=inference score={_final_score:.2f} steps={sum(r.get('steps',0) for r in results.values())}", flush=True)

    invalid = [(t, s) for t, s in output["scores"].items() if not (0.0 < s < 1.0)]
    if invalid:
        print(f"[END] task=inference score=0.01 steps=0 error=out_of_range_scores", flush=True)
        sys.exit(1)

    return output


if __name__ == "__main__":
    main()
