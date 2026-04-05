---
title: Email Ops Agent
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "3.10"
app_file: main.py
pinned: false
---

# Email Operations Agent

This project runs an AI-powered email operations system using LLM-based decision making.

## Features
- Intent extraction
- Email routing
- Automated replies
- Escalation handling

## Usage
Run the app using Hugging Face Spaces.
# 📧 Email Operations Center — OpenEnv v2

A real-world agentic AI environment where agents learn to manage a **dynamic business inbox** with SLA timers, tool use, policy constraints, adversarial noise, and chain-of-thought workflows.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-2.0-blue)](https://openenv.dev)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-orange)](https://fastapi.tiangolo.com)

---

## 🌍 What Makes This Environment Novel

| Feature | Description |
|---------|-------------|
| **Chain-of-thought workflow** | Agent must extract intent → query tools → then act |
| **Mock CRM + ticket + order tools** | Agent looks up customer history, open tickets, order status before deciding |
| **SLA timers** | Every email has a deadline — reward decays if agent is slow |
| **Policy engine** | Emails tagged with rules: `no_auto_reply`, `must_escalate`, `compliance_review` |
| **Dynamic inbox** | New emails arrive mid-episode — agent must reprioritize |
| **Multi-label routing** | 8 departments: support, billing, legal, engineering, sales, hr, compliance, executive |
| **Adversarial noise** | Spam, phishing, emotional manipulation, incomplete threads, repeated escalations |
| **4 scenario types** | Startup support, HR department, healthcare admin, university admissions |
| **Financial impact signals** | Emails tagged with revenue at risk ($0–$500k) — affects urgency scoring |
| **5-signal reward** | Routing accuracy, SLA speed, reply quality, policy compliance, tool relevance |

---

## 🎮 Agent Workflow

The agent must follow this chain-of-thought structure:

```
1. select_email      → pick most urgent email from inbox
2. extract_intent    → identify what sender wants + urgency level
3. lookup_customer   → query CRM for customer context (if applicable)
   lookup_ticket     → check existing support tickets
   lookup_order      → verify order/billing details
4. Terminal action:
   → route           → send to correct department
   → reply           → draft response (if allowed by policy)
   → escalate        → flag for senior team
   → request_clarification → ask sender for more info
   → archive         → close low-priority thread
   → delete          → remove spam/phishing
   → flag_policy_violation → mark for compliance review
```

---

## 🏆 Tasks

### `task_easy` — Startup Support Inbox
- **8 emails**, clear categories, no SLA pressure
- Agent learns: basic routing, tool lookup, reply quality
- Expected baseline: 0.45–0.65

### `task_medium` — HR Department Inbox
- **15 emails**, SLA timers, dynamic arrivals, policy rules
- Includes: harassment complaint, legal dispute, emotional resignation, repeated threads
- Agent learns: urgency detection, policy compliance, reprioritization
- Expected baseline: 0.35–0.55

### `task_hard` — Healthcare Admin + Adversarial
- **25 emails**, strict HIPAA/compliance policies, adversarial noise, high-stakes cases
- Includes: data breaches, $180k churn risk, legal threats, phishing, incomplete threads
- Agent learns: high-stakes decision making, policy over urgency, tool use before action
- Expected baseline: 0.25–0.45

---

## 📊 Reward Function — 5 Signals

| Signal | Weight | Description |
|--------|--------|-------------|
| Routing accuracy | 40% (easy) / 25% (hard) | Correct department routing |
| Reply quality | 25% | Keyword matching in responses |
| Tool use correctness | 20% | Called right tool for email context |
| Policy compliance | 15% | No auto-replies on blocked emails, proper escalation |
| SLA performance | 10% | Email handled before deadline |
| **Completion bonus** | up to +0.40 | Finishing all emails with accuracy |

Policy violations are **heavily penalized**: −0.20 to −0.30 per violation.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start episode `{"task_id": "task_easy", "seed": 42}` |
| `POST` | `/step` | Execute action |
| `GET` | `/state` | Current observation |
| `GET` | `/tasks` | List all tasks |
| `GET` | `/tools` | Available CRM/ticket/order tools |
| `GET` | `/grade` | Score current episode |
| `GET` | `/validate` | OpenEnv compliance check |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Run server
python main.py

# Test manually
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d "{\"task_id\":\"task_easy\",\"seed\":42}"

# Run inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="hf_..."
export ENV_BASE_URL="http://localhost:7860"
python inference.py

# Validate
python validate.py --env-url http://localhost:7860
```

---

## 🐳 Docker

```bash
docker build -t email-ops-env .
docker run -p 7860:7860 email-ops-env
```

---

## 📁 Project Structure

```
email-ops-env/
├── main.py               # FastAPI server
├── inference.py          # Baseline LLM + rule-based agent
├── validate.py           # Pre-submission validator
├── openenv.yaml          # OpenEnv spec
├── Dockerfile
├── requirements.txt
├── README.md
├── env/
│   ├── models.py         # Typed Pydantic models
│   └── environment.py    # Core env logic (SLA, tools, policy)
├── scenarios/
│   └── emails.py         # 48 emails across 3 difficulty tiers
├── tools/
│   └── crm.py            # Mock CRM, ticket, order lookups
└── graders/
    └── graders.py        # Task graders (0.0–1.0)
```

---

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | LLM API endpoint |
| `MODEL_NAME` | Model identifier |
| `HF_TOKEN` | API key |
| `ENV_BASE_URL` | Environment server URL |

---

## 🤖 Agent Tips

1. **Always follow the chain-of-thought**: select → extract → tool → act
2. **Check `policy_rules` before replying** — `no_auto_reply` emails must be routed/escalated
3. **`must_escalate` overrides everything** — even if you know the answer
4. **VIP + financial impact = treat as critical** — check CRM first
5. **Spam/phishing → delete immediately** — don't waste steps on it
6. **SLA is ticking** — resolve critical emails first (lowest `sla_remaining`)
7. **Tool calls are rewarded** — always look up context for emails mentioning ticket/order IDs

---

## License
MIT
=======
---
title: Email Ops Env
emoji: 🐢
colorFrom: indigo
colorTo: yellow
sdk: docker
pinned: false
short_description: Meta OpenEnv Hackathon
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

