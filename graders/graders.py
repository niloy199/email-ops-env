"""
Graders for Email Operations Center v2.
All scores strictly within (0.001, 0.999) — never exactly 0.0 or 1.0.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
from env.models import (
    Email, Urgency, RouteDept, PolicyRule, ActionType, EmailStatus
)

# Score must be strictly between 0 and 1 — never exactly 0.0 or 1.0
MIN_SCORE = 0.001
MAX_SCORE = 0.999

EPS = 1e-6
def clamp(score: float) -> float:
    return max(EPS, min(1.0 - EPS, score))


class BaseGrader:

    def _routing_score(self, e: Email) -> float:
        if e.agent_route is None:
            return 0.05
        if e.agent_route == e.true_route:
            return 0.99
        adjacency = {
            RouteDept.LEGAL:       [RouteDept.COMPLIANCE, RouteDept.EXECUTIVE],
            RouteDept.COMPLIANCE:  [RouteDept.LEGAL, RouteDept.HR],
            RouteDept.SUPPORT:     [RouteDept.ENGINEERING, RouteDept.BILLING],
            RouteDept.ENGINEERING: [RouteDept.SUPPORT],
            RouteDept.EXECUTIVE:   [RouteDept.LEGAL, RouteDept.SALES],
        }
        if e.agent_route in adjacency.get(e.true_route, []):
            return 0.4
        return 0.05

    def _urgency_score(self, e: Email) -> float:
        if e.agent_urgency is None:
            return 0.05
        if e.agent_urgency == e.true_urgency:
            return 0.99
        order = [Urgency.LOW, Urgency.MEDIUM, Urgency.HIGH, Urgency.CRITICAL]
        try:
            diff = abs(order.index(e.agent_urgency) - order.index(e.true_urgency))
            return max(0.05, 0.99 - diff * 0.35)
        except ValueError:
            return 0.05

    def _policy_score(self, e: Email) -> float:
        violations = 0
        total_rules = max(1, len(e.policy_rules))
        for rule in e.policy_rules:
            if rule == PolicyRule.NO_AUTO_REPLY and e.agent_action == ActionType.REPLY:
                violations += 1
            if rule == PolicyRule.MUST_ESCALATE and e.agent_action not in (
                ActionType.ESCALATE, ActionType.FLAG_POLICY_VIOLATION,
                ActionType.ROUTE,
            ):
                violations += 1
            if rule == PolicyRule.COMPLIANCE_REVIEW and e.agent_route not in (
                RouteDept.COMPLIANCE, RouteDept.LEGAL
            ):
                violations += 0.5
        raw = max(0.05, 0.99 - violations / total_rules)
        return raw

    def _tool_score(self, e: Email) -> float:
        if not e.requires_tool:
            return 0.99 if not e.tool_was_called else 0.7
        return 0.99 if e.tool_was_called else 0.05

    def _sla_score(self, e: Email) -> float:
        return 0.05 if e.sla_breached else 0.99

    def _reply_score(self, e: Email) -> float:
        if not e.requires_reply:
            return 0.99
        if not e.agent_reply:
            return 0.05
        kws = e.expected_reply_keywords
        if not kws:
            return 0.5
        matched = sum(1 for kw in kws if kw.lower() in e.agent_reply.lower())
        score = max(0.05, matched / len(kws))
        return round(score, 4)

    def _adversarial_score(self, e: Email) -> float:
        if not e.is_adversarial:
            return 0.99
        atype = e.adversarial_type
        if atype in ("spam", "phishing", "incomplete_thread"):
            return 0.99 if e.agent_action == ActionType.DELETE else 0.05
        if atype == "emotionally_charged":
            return 0.8 if e.agent_route == e.true_route else 0.2
        if atype == "repeated_thread":
            return 0.99 if e.tool_was_called else 0.5
        return 0.5


class EasyTaskGrader(BaseGrader):

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return MIN_SCORE, {"error": "no_emails_processed", "final_score": MIN_SCORE}

        routing     = [self._routing_score(e) for e in processed]
        replies     = [self._reply_score(e) for e in processed]
        tools       = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [0.5]
        coverage    = min(0.999, len(processed) / 8)

        avg_routing     = sum(routing) / len(routing)
        avg_reply       = sum(replies) / len(replies)
        avg_tool        = sum(tools) / len(tools)
        avg_adversarial = sum(adversarial) / len(adversarial)

        raw = (
            avg_routing     * 0.40 +
            avg_reply       * 0.25 +
            avg_tool        * 0.20 +
            avg_adversarial * 0.05 +
            coverage        * 0.10
        )
        score = clamp(raw)
        return score, {
            "task": "task_easy",
            "emails_processed": len(processed),
            "avg_routing":           round(avg_routing, 4),
            "avg_reply":             round(avg_reply, 4),
            "avg_tool_use":          round(avg_tool, 4),
            "adversarial_handling":  round(avg_adversarial, 4),
            "coverage":              round(coverage, 4),
            "final_score":           score,
        }


class MediumTaskGrader(BaseGrader):

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return MIN_SCORE, {"error": "no_emails_processed", "final_score": MIN_SCORE}

        routing     = [self._routing_score(e) for e in processed]
        urgency     = [self._urgency_score(e) for e in processed]
        sla         = [self._sla_score(e) for e in processed]
        replies     = [self._reply_score(e) for e in processed]
        tools       = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [0.5]
        coverage    = min(0.999, len(processed) / 15)

        critical = [e for e in processed if e.true_urgency == Urgency.CRITICAL]
        critical_score = sum(
            1 for e in critical
            if e.agent_action in (ActionType.ESCALATE, ActionType.ROUTE, ActionType.FLAG_POLICY_VIOLATION)
        ) / max(1, len(critical))
        critical_score = max(0.05, critical_score)

        policy_emails = [e for e in processed if e.policy_rules]
        policy_compliance = sum(
            self._policy_score(e) for e in policy_emails
        ) / max(1, len(policy_emails)) if policy_emails else 0.5

        avg = lambda lst: sum(lst) / len(lst)
        raw = (
            avg(routing)      * 0.25 +
            avg(urgency)      * 0.10 +
            policy_compliance * 0.15 +
            avg(sla)          * 0.10 +
            avg(replies)      * 0.15 +
            avg(tools)        * 0.10 +
            critical_score    * 0.10 +
            avg(adversarial)  * 0.03 +
            coverage          * 0.02
        )
        score = clamp(raw)
        return score, {
            "task": "task_medium",
            "emails_processed":  len(processed),
            "avg_routing":       round(avg(routing), 4),
            "avg_urgency":       round(avg(urgency), 4),
            "policy_compliance": round(policy_compliance, 4),
            "avg_sla":           round(avg(sla), 4),
            "avg_reply":         round(avg(replies), 4),
            "avg_tool_use":      round(avg(tools), 4),
            "critical_handling": round(critical_score, 4),
            "adversarial_handling": round(avg(adversarial), 4),
            "coverage":          round(coverage, 4),
            "final_score":       score,
        }


class HardTaskGrader(BaseGrader):

    HIGH_STAKES_IDS = {
        "hc_001", "hc_003", "hc_005", "hc_007", "hc_009",
        "hc_013", "hc_015", "h1_003", "h1_009", "h1_014",
    }

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return MIN_SCORE, {"error": "no_emails_processed", "final_score": MIN_SCORE}

        routing     = [self._routing_score(e) for e in processed]
        urgency     = [self._urgency_score(e) for e in processed]
        sla         = [self._sla_score(e) for e in processed]
        replies     = [self._reply_score(e) for e in processed]
        tools       = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [0.5]
        coverage    = min(0.999, len(processed) / 25)

        hs = [e for e in processed if e.id in self.HIGH_STAKES_IDS]
        hs_score = 0.05
        if hs:
            hs_routing = sum(self._routing_score(e) for e in hs) / len(hs)
            hs_policy  = sum(self._policy_score(e) for e in hs) / len(hs)
            hs_tool    = sum(self._tool_score(e) for e in hs) / len(hs)
            hs_score   = max(0.05, hs_routing * 0.4 + hs_policy * 0.4 + hs_tool * 0.2)

        cot_score = sum(
            1 for e in processed
            if e.agent_intent is not None and e.agent_route is not None
        ) / max(1, len(processed))
        cot_score = max(0.05, cot_score)

        policy_emails = [e for e in processed if e.policy_rules]
        policy_compliance = sum(
            self._policy_score(e) for e in policy_emails
        ) / max(1, len(policy_emails)) if policy_emails else 0.5

        avg = lambda lst: sum(lst) / len(lst)
        raw = (
            avg(routing)      * 0.20 +
            avg(urgency)      * 0.08 +
            policy_compliance * 0.15 +
            avg(sla)          * 0.08 +
            avg(replies)      * 0.10 +
            avg(tools)        * 0.12 +
            hs_score          * 0.12 +
            cot_score         * 0.08 +
            avg(adversarial)  * 0.05 +
            coverage          * 0.02
        )
        score = clamp(raw)
        return score, {
            "task": "task_hard",
            "emails_processed":      len(processed),
            "avg_routing":           round(avg(routing), 4),
            "avg_urgency":           round(avg(urgency), 4),
            "policy_compliance":     round(policy_compliance, 4),
            "avg_sla":               round(avg(sla), 4),
            "avg_reply":             round(avg(replies), 4),
            "avg_tool_use":          round(avg(tools), 4),
            "high_stakes_score":     round(hs_score, 4),
            "chain_of_thought_score":round(cot_score, 4),
            "adversarial_handling":  round(avg(adversarial), 4),
            "coverage":              round(coverage, 4),
            "final_score":           score,
        }


GRADERS = {
    "task_easy":   EasyTaskGrader(),
    "task_medium": MediumTaskGrader(),
    "task_hard":   HardTaskGrader(),
}


def grade_episode(task_id: str, processed: list) -> Tuple[float, Dict]:
    if task_id not in GRADERS:
        return MIN_SCORE, {"error": f"Unknown task: {task_id}"}
    return GRADERS[task_id].grade(processed)