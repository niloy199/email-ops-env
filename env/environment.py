"""
EmailOpsEnv — Core OpenEnv v2 environment.
Features: SLA timers, tool use, policy engine, dynamic arrivals,
chain-of-thought workflow, multi-label routing.
"""
from __future__ import annotations
import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from env.models import (
    Action, ActionType, Email, EmailStatus, Observation,
    PolicyRule, Reward, RouteDept, StepResponse, TaskInfo, Urgency,
)
from scenarios.emails import SCENARIO_EMAILS, SCENARIO_NAMES
from tools.crm import lookup_customer, lookup_ticket, lookup_order

TASK_CONFIG: Dict[str, Dict] = {
    "task_easy": {
        "name": "Startup Support Inbox",
        "difficulty": "easy",
        "description": "8 emails from a SaaS startup support queue.",
        "num_emails": 8, "max_steps": 60,
        "scenario": "startup_support",
        "sla_penalty_per_step": 0.03,
        "policy_penalty": 0.20,
    },
    "task_medium": {
        "name": "HR Department Inbox",
        "difficulty": "medium",
        "description": "15 HR emails with SLA, dynamic arrivals, and policy rules.",
        "num_emails": 15, "max_steps": 150,
        "scenario": "hr_department",
        "sla_penalty_per_step": 0.04,
        "policy_penalty": 0.25,
    },
    "task_hard": {
        "name": "Healthcare Admin + Adversarial",
        "difficulty": "hard",
        "description": "25 emails with strict HIPAA policies, adversarial noise, tool use.",
        "num_emails": 25, "max_steps": 300,
        "scenario": "healthcare_admin",
        "sla_penalty_per_step": 0.05,
        "policy_penalty": 0.30,
    },
}

# Reward constants
R_CORRECT_ROUTE      = 0.20
R_WRONG_ROUTE        = -0.12
R_CORRECT_URGENCY    = 0.10
R_WRONG_URGENCY      = -0.06
R_QUALITY_REPLY_MAX  = 0.25
R_TOOL_USED_CORRECT  = 0.10
R_TOOL_USED_WRONG    = -0.03
R_POLICY_CORRECT     = 0.15
R_SELECT             = 0.01
R_EXTRACT_INTENT     = 0.05
R_CLARIFICATION_OK   = 0.08
R_COMPLETION_BONUS   = 0.40


class EmailOpsEnv:
    def __init__(self):
        self._task_id = "task_easy"
        self._all_emails: List[Email] = []
        self._inbox: List[Email] = []
        self._processed: List[Email] = []
        self._current: Optional[Email] = None
        self._step = 0
        self._max_steps = 60
        self._done = False
        self._seed: Optional[int] = None
        self._scenario = "startup_support"
        self._last_tool_result = None
        self._cfg: Dict = {}
        self._cumulative_reward = 0.0

    # ── OpenEnv Interface ──────────────────────────────────────────────────────

    def reset(self, task_id: str = "task_easy", seed: Optional[int] = None) -> Observation:
        if task_id not in TASK_CONFIG:
            raise ValueError(f"Unknown task: {task_id}")
        self._task_id = task_id
        self._cfg = TASK_CONFIG[task_id]
        self._seed = seed
        if seed is not None:
            random.seed(seed)

        raw = SCENARIO_EMAILS[task_id]
        self._all_emails = [copy.deepcopy(e) for e in raw]
        # Start with emails that arrive at step 0
        self._inbox = [e for e in self._all_emails if e.arrival_step == 0]
        self._processed = []
        self._current = None
        self._step = 0
        self._max_steps = self._cfg["max_steps"]
        self._done = False
        self._scenario = self._cfg["scenario"]
        self._last_tool_result = None
        self._cumulative_reward = 0.0
        return self.state()

    def step(self, action: Action) -> StepResponse:
        if self._done:
            return StepResponse(
                observation=self.state(),
                reward=Reward(value=0.01, message="Episode done"),
                done=True, info={"error": "episode_done"},
            )
        self._step += 1
        self._tick_sla()
        self._deliver_arrivals()
        reward, info = self._execute(action)
        self._cumulative_reward += reward.value

        if not self._inbox and self._current is None:
            self._done = True
            bonus = self._completion_bonus()
            reward.value = min(0.99, reward.value + bonus)
            reward.breakdown["completion_bonus"] = bonus
            reward.message += f" | Complete! Bonus +{bonus:.2f}"

        if self._step >= self._max_steps:
            self._done = True

        obs = self.state()
        obs.done = self._done
        info.update({
            "step": self._step,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "inbox_remaining": len(self._inbox),
            "processed": len(self._processed),
        })
        return StepResponse(observation=obs, reward=reward, done=self._done, info=info)

    def state(self) -> Observation:
        breached = [e.id for e in self._all_emails if e.sla_breached]
        pending = sum(
            1 for e in self._all_emails
            if e.arrival_step > self._step and e.status == EmailStatus.PENDING
        )
        return Observation(
            inbox=list(self._inbox),
            processed=list(self._processed),
            current_email=self._current,
            tool_results=self._last_tool_result,
            step_count=self._step,
            inbox_size=len(self._all_emails),
            sla_breached=breached,
            pending_arrivals=pending,
            scenario=self._scenario,
            done=self._done,
            task_id=self._task_id,
            message=(
                f"Step {self._step}/{self._max_steps} | "
                f"Inbox: {len(self._inbox)} | "
                f"Processed: {len(self._processed)} | "
                f"SLA breached: {len(breached)}"
            ),
        )

    # ── SLA + Dynamic Arrivals ─────────────────────────────────────────────────

    def _tick_sla(self):
        """Decrement SLA timers each step for unprocessed emails."""
        for email in self._inbox:
            if email.status in (EmailStatus.PENDING, EmailStatus.SELECTED):
                email.sla_remaining = max(0, email.sla_remaining - 1)
                if email.sla_remaining == 0 and not email.sla_breached:
                    email.sla_breached = True
                    email.status = EmailStatus.BREACHED

    def _deliver_arrivals(self):
        """Deliver emails scheduled to arrive at this step."""
        for email in self._all_emails:
            if email.arrival_step == self._step and email not in self._inbox and email not in self._processed:
                self._inbox.append(email)

    # ── Action Dispatch ────────────────────────────────────────────────────────

    def _execute(self, action: Action) -> Tuple[Reward, Dict]:
        info: Dict[str, Any] = {"action": action.action_type}

        if action.action_type == ActionType.SELECT_EMAIL:
            return self._select(action, info)

        if self._current is None:
            return Reward(value=-0.05, message="No email selected. Use select_email first."), info

        dispatch = {
            ActionType.EXTRACT_INTENT:        self._extract_intent,
            ActionType.LOOKUP_CUSTOMER:       self._tool_lookup,
            ActionType.LOOKUP_TICKET:         self._tool_lookup,
            ActionType.LOOKUP_ORDER:          self._tool_lookup,
            ActionType.REPLY:                 self._reply,
            ActionType.ESCALATE:              self._escalate,
            ActionType.ROUTE:                 self._route,
            ActionType.SCHEDULE_FOLLOWUP:     self._schedule,
            ActionType.REQUEST_CLARIFICATION: self._clarify,
            ActionType.ARCHIVE:               self._archive,
            ActionType.FLAG_POLICY_VIOLATION: self._flag_policy,
            ActionType.DELETE:                self._delete,
        }
        fn = dispatch.get(action.action_type)
        if fn:
            return fn(action, info)
        return Reward(value=-0.03, message="Unknown action"), info

    def _select(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        if action.email_id:
            email = next((e for e in self._inbox if e.id == action.email_id), None)
        else:
            # Auto-select highest urgency email
            priority = {Urgency.CRITICAL: 4, Urgency.HIGH: 3, Urgency.MEDIUM: 2, Urgency.LOW: 1}
            pending = [e for e in self._inbox if e.status in (EmailStatus.PENDING, EmailStatus.BREACHED)]
            if not pending:
                return Reward(value=-0.02, message="No emails to select"), info
            email = sorted(pending, key=lambda e: (
                -(e.sla_remaining == 0),
                -priority.get(e.true_urgency or Urgency.LOW, 0),
                e.arrival_step,
            ))[0]

        if not email:
            return Reward(value=-0.05, message="Email not found"), info

        email.status = EmailStatus.SELECTED
        self._current = email
        self._last_tool_result = None
        info["selected"] = email.id
        return Reward(value=R_SELECT, message=f"Selected: {email.subject[:50]}"), info

    def _extract_intent(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        email.status = EmailStatus.WORKING
        if action.intent:
            email.agent_intent = action.intent
            # Partial reward for extraction step
            return Reward(
                value=R_EXTRACT_INTENT,
                message=f"Intent extracted: {action.intent}",
            ), info
        return Reward(value=0.01, message="Intent step taken (no intent provided)"), info

    def _tool_lookup(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        email.tool_was_called = True

        tool_map = {
            ActionType.LOOKUP_CUSTOMER: ("lookup_customer", lookup_customer),
            ActionType.LOOKUP_TICKET:   ("lookup_ticket",   lookup_ticket),
            ActionType.LOOKUP_ORDER:    ("lookup_order",    lookup_order),
        }
        tool_name, fn = tool_map[action.action_type]
        qid = action.lookup_id or action.email_id or ""
        result = fn(qid)
        self._last_tool_result = result
        info["tool"] = tool_name
        info["found"] = result.found

        # Score: was this the right tool for this email?
        correct_tool = email.required_tool == tool_name if email.required_tool else False
        score = R_TOOL_USED_CORRECT if correct_tool else R_TOOL_USED_WRONG
        msg = (
            f"Tool {tool_name}: {'found' if result.found else 'not found'}. "
            f"{'Relevant' if correct_tool else 'Not the required tool'}."
        )
        return Reward(value=score, message=msg, breakdown={"tool": score}), info

    def _reply(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        if not action.reply_text or len(action.reply_text.strip()) < 20:
            self._finalize(email, ActionType.REPLY)
            return Reward(value=-0.15, message="Reply too short"), info

        # Check policy: NO_AUTO_REPLY
        if PolicyRule.NO_AUTO_REPLY in email.policy_rules:
            self._finalize(email, ActionType.REPLY)
            return Reward(
                value=-self._cfg["policy_penalty"],
                message="POLICY VIOLATION: This email must not be auto-replied",
                breakdown={"policy_violation": -self._cfg["policy_penalty"]},
            ), info

        if not email.requires_reply:
            self._finalize(email, ActionType.REPLY)
            return Reward(value=-0.05, message="Unnecessary reply"), info

        # Keyword quality score
        reply_lower = action.reply_text.lower()
        kws = email.expected_reply_keywords
        matched = sum(1 for kw in kws if kw.lower() in reply_lower) if kws else 0
        kw_score = matched / max(1, len(kws))
        length = len(action.reply_text.split())
        length_bonus = 0.05 if 25 <= length <= 350 else 0.0
        score = round(kw_score * R_QUALITY_REPLY_MAX + length_bonus, 4)
        score = max(0.01, min(0.99, score))

        email.agent_reply = action.reply_text
        self._finalize(email, ActionType.REPLY)
        return Reward(
            value=score,
            message=f"Reply quality: {kw_score:.0%} kw match ({matched}/{len(kws)})",
            breakdown={"reply_quality": score},
        ), info

    def _escalate(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        should_escalate = (
            PolicyRule.MUST_ESCALATE in email.policy_rules or
            email.true_urgency in (Urgency.CRITICAL, Urgency.HIGH)
        )
        score = 0.18 if should_escalate else -0.08
        msg = "Correct escalation" if should_escalate else "Unnecessary escalation"
        self._finalize(email, ActionType.ESCALATE)
        return Reward(value=score, message=msg), info

    def _route(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        breakdown = {}
        total = 0.0

        # Routing accuracy
        if action.route_to == email.true_route:
            breakdown["routing"] = R_CORRECT_ROUTE
            msg = f"Correct route → {action.route_to}"
        else:
            breakdown["routing"] = R_WRONG_ROUTE
            msg = f"Wrong route → {action.route_to} (expected {email.true_route})"
        total += breakdown["routing"]

        # Urgency accuracy
        if action.urgency:
            email.agent_urgency = action.urgency
            if action.urgency == email.true_urgency:
                breakdown["urgency"] = R_CORRECT_URGENCY
                msg += " | Urgency correct"
            else:
                breakdown["urgency"] = R_WRONG_URGENCY
                msg += f" | Urgency wrong (got {action.urgency}, expected {email.true_urgency})"
            total += breakdown["urgency"]

        # Policy: MUST_ESCALATE but routed to non-escalation dept
        if PolicyRule.MUST_ESCALATE in email.policy_rules and action.route_to not in (
            RouteDept.LEGAL, RouteDept.COMPLIANCE, RouteDept.EXECUTIVE
        ):
            penalty = -self._cfg["policy_penalty"]
            breakdown["policy"] = penalty
            total += penalty
            msg += f" | POLICY VIOLATION: must escalate ({penalty:.2f})"

        email.agent_route = action.route_to
        self._finalize(email, ActionType.ROUTE)
        score = max(-0.99, min(0.99, total))
        return Reward(value=round(score, 4), message=msg, breakdown=breakdown), info

    def _schedule(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        hours = action.followup_hours or 24
        score = 0.08 if email.requires_clarification or not email.requires_reply else 0.02
        self._finalize(email, ActionType.SCHEDULE_FOLLOWUP)
        return Reward(value=score, message=f"Follow-up scheduled in {hours}h"), info

    def _clarify(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        score = R_CLARIFICATION_OK if email.requires_clarification else -0.03
        msg = "Correct: clarification needed" if email.requires_clarification else "Unnecessary clarification"
        self._finalize(email, ActionType.REQUEST_CLARIFICATION)
        return Reward(value=score, message=msg), info

    def _archive(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        should_archive = (
            not email.requires_reply and
            email.true_urgency == Urgency.LOW and
            not email.policy_rules
        )
        score = 0.08 if should_archive else -0.06
        msg = "Correct archive" if should_archive else "Premature archive (action required)"
        self._finalize(email, ActionType.ARCHIVE)
        return Reward(value=score, message=msg), info

    def _flag_policy(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        email.policy_flagged = True
        has_policy = bool(email.policy_rules)
        score = R_POLICY_CORRECT if has_policy else -0.05
        msg = "Correct policy flag" if has_policy else "False policy flag"
        self._finalize(email, ActionType.FLAG_POLICY_VIOLATION)
        return Reward(value=score, message=msg), info

    def _delete(self, action: Action, info: Dict) -> Tuple[Reward, Dict]:
        email = self._current
        is_spam = email.is_adversarial and email.adversarial_type in ("spam", "phishing", "incomplete_thread")
        score = 0.10 if is_spam else -0.15
        msg = "Correct delete (spam/phishing)" if is_spam else "Wrong delete (not spam)"
        self._finalize(email, ActionType.DELETE)
        return Reward(value=score, message=msg), info

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _finalize(self, email: Email, action: ActionType):
        email.agent_action = action
        email.status = EmailStatus.COMPLETED
        email.steps_taken = self._step
        if email in self._inbox:
            self._inbox.remove(email)
        self._processed.append(email)
        self._current = None
        self._last_tool_result = None

    def _completion_bonus(self) -> float:
        if not self._processed:
            return 0.0
        n = len(self._processed)
        correct_route   = sum(1 for e in self._processed if e.agent_route == e.true_route) / n
        tool_compliance = sum(
            1 for e in self._processed
            if e.requires_tool == e.tool_was_called
        ) / n
        no_policy_viol  = sum(
            1 for e in self._processed
            if not (PolicyRule.NO_AUTO_REPLY in e.policy_rules and e.agent_action == ActionType.REPLY)
        ) / n
        coverage = min(0.99, n / len(self._all_emails))
        bonus = R_COMPLETION_BONUS * (
            correct_route   * 0.35 +
            tool_compliance * 0.25 +
            no_policy_viol  * 0.25 +
            coverage        * 0.15
        )
        return round(bonus, 4)

    def get_tasks(self) -> List[TaskInfo]:
        return [
            TaskInfo(id=tid, **{k: v for k, v in cfg.items() if k in TaskInfo.model_fields})
            for tid, cfg in TASK_CONFIG.items()
        ]
