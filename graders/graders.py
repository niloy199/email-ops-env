"""
Graders for Email Operations Center v2.
Deterministic, programmatic scoring 0.0–1.0.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
from env.models import (
    Email, Urgency, RouteDept, PolicyRule, ActionType, EmailStatus
)


class BaseGrader:

    def _routing_score(self, e: Email) -> float:
        if e.agent_route is None:
            return 0.0
        if e.agent_route == e.true_route:
            return 1.0
        # Adjacent departments get partial credit
        adjacency = {
            RouteDept.LEGAL: [RouteDept.COMPLIANCE, RouteDept.EXECUTIVE],
            RouteDept.COMPLIANCE: [RouteDept.LEGAL, RouteDept.HR],
            RouteDept.SUPPORT: [RouteDept.ENGINEERING, RouteDept.BILLING],
            RouteDept.ENGINEERING: [RouteDept.SUPPORT],
            RouteDept.EXECUTIVE: [RouteDept.LEGAL, RouteDept.SALES],
        }
        if e.agent_route in adjacency.get(e.true_route, []):
            return 0.4
        return 0.0

    def _urgency_score(self, e: Email) -> float:
        if e.agent_urgency is None:
            return 0.0
        if e.agent_urgency == e.true_urgency:
            return 1.0
        order = [Urgency.LOW, Urgency.MEDIUM, Urgency.HIGH, Urgency.CRITICAL]
        try:
            diff = abs(order.index(e.agent_urgency) - order.index(e.true_urgency))
            return max(0.0, 1.0 - diff * 0.35)
        except ValueError:
            return 0.0

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
        return max(0.0, 1.0 - violations / total_rules)

    def _tool_score(self, e: Email) -> float:
        if not e.requires_tool:
            return 1.0 if not e.tool_was_called else 0.7
        return 1.0 if e.tool_was_called else 0.0

    def _sla_score(self, e: Email) -> float:
        return 0.0 if e.sla_breached else 1.0

    def _reply_score(self, e: Email) -> float:
        if not e.requires_reply:
            return 1.0
        if not e.agent_reply:
            return 0.0
        kws = e.expected_reply_keywords
        if not kws:
            return 0.5
        matched = sum(1 for kw in kws if kw.lower() in e.agent_reply.lower())
        return round(matched / len(kws), 4)

    def _adversarial_score(self, e: Email) -> float:
        if not e.is_adversarial:
            return 1.0
        atype = e.adversarial_type
        if atype in ("spam", "phishing", "incomplete_thread"):
            return 1.0 if e.agent_action == ActionType.DELETE else 0.0
        if atype == "emotionally_charged":
            # Should route correctly without over-reacting
            return 0.8 if e.agent_route == e.true_route else 0.2
        if atype == "repeated_thread":
            return 1.0 if e.tool_was_called else 0.5
        return 0.5


class EasyTaskGrader(BaseGrader):
    """Grader for task_easy — focuses on routing, basic tool use, reply quality."""

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return 0.0, {"error": "no_emails_processed"}

        routing   = [self._routing_score(e) for e in processed]
        replies   = [self._reply_score(e) for e in processed]
        tools     = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [1.0]
        coverage  = min(1.0, len(processed) / 8)

        avg_routing    = sum(routing) / len(routing)
        avg_reply      = sum(replies) / len(replies)
        avg_tool       = sum(tools) / len(tools)
        avg_adversarial = sum(adversarial) / len(adversarial)

        score = (
            avg_routing    * 0.40 +
            avg_reply      * 0.25 +
            avg_tool       * 0.20 +
            avg_adversarial* 0.05 +
            coverage       * 0.10
        )
        return round(score, 4), {
            "task": "task_easy", "emails_processed": len(processed),
            "avg_routing": round(avg_routing, 4),
            "avg_reply": round(avg_reply, 4),
            "avg_tool_use": round(avg_tool, 4),
            "adversarial_handling": round(avg_adversarial, 4),
            "coverage": round(coverage, 4),
            "final_score": round(score, 4),
        }


class MediumTaskGrader(BaseGrader):
    """Grader for task_medium — adds policy, SLA, urgency, dynamic handling."""

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return 0.0, {"error": "no_emails_processed"}

        routing   = [self._routing_score(e) for e in processed]
        urgency   = [self._urgency_score(e) for e in processed]
        policy    = [self._policy_score(e) for e in processed]
        sla       = [self._sla_score(e) for e in processed]
        replies   = [self._reply_score(e) for e in processed]
        tools     = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [1.0]
        coverage  = min(1.0, len(processed) / 15)

        # Critical email handling
        critical = [e for e in processed if e.true_urgency == Urgency.CRITICAL]
        critical_score = sum(
            1 for e in critical
            if e.agent_action in (ActionType.ESCALATE, ActionType.ROUTE, ActionType.FLAG_POLICY_VIOLATION)
        ) / max(1, len(critical))

        # Policy compliance
        policy_emails = [e for e in processed if e.policy_rules]
        policy_compliance = sum(
            self._policy_score(e) for e in policy_emails
        ) / max(1, len(policy_emails))

        avg = lambda lst: sum(lst) / len(lst)
        score = (
            avg(routing)    * 0.25 +
            avg(urgency)    * 0.10 +
            policy_compliance * 0.15 +
            avg(sla)        * 0.10 +
            avg(replies)    * 0.15 +
            avg(tools)      * 0.10 +
            critical_score  * 0.10 +
            avg(adversarial)* 0.03 +
            coverage        * 0.02
        )
        return round(score, 4), {
            "task": "task_medium", "emails_processed": len(processed),
            "avg_routing": round(avg(routing), 4),
            "avg_urgency": round(avg(urgency), 4),
            "policy_compliance": round(policy_compliance, 4),
            "avg_sla": round(avg(sla), 4),
            "avg_reply": round(avg(replies), 4),
            "avg_tool_use": round(avg(tools), 4),
            "critical_handling": round(critical_score, 4),
            "adversarial_handling": round(avg(adversarial), 4),
            "coverage": round(coverage, 4),
            "final_score": round(score, 4),
        }


class HardTaskGrader(BaseGrader):
    """Grader for task_hard — full scoring: HIPAA, financial impact, adversarial, chain-of-thought."""

    HIGH_STAKES_IDS = {
        "hc_001", "hc_003", "hc_005", "hc_007", "hc_009",
        "hc_013", "hc_015", "h1_003", "h1_009", "h1_014",
    }

    def grade(self, processed: List[Email]) -> Tuple[float, Dict]:
        if not processed:
            return 0.0, {"error": "no_emails_processed"}

        routing     = [self._routing_score(e) for e in processed]
        urgency     = [self._urgency_score(e) for e in processed]
        policy      = [self._policy_score(e) for e in processed]
        sla         = [self._sla_score(e) for e in processed]
        replies     = [self._reply_score(e) for e in processed]
        tools       = [self._tool_score(e) for e in processed]
        adversarial = [self._adversarial_score(e) for e in processed if e.is_adversarial] or [1.0]
        coverage    = min(1.0, len(processed) / 25)

        # High-stakes email handling (financial impact > $10k or policy-critical)
        hs = [e for e in processed if e.id in self.HIGH_STAKES_IDS]
        hs_score = 0.0
        if hs:
            hs_routing = sum(self._routing_score(e) for e in hs) / len(hs)
            hs_policy  = sum(self._policy_score(e) for e in hs) / len(hs)
            hs_tool    = sum(self._tool_score(e) for e in hs) / len(hs)
            hs_score   = (hs_routing * 0.4 + hs_policy * 0.4 + hs_tool * 0.2)

        # Chain-of-thought: were intents extracted before routing?
        cot_score = sum(
            1 for e in processed
            if e.agent_intent is not None and e.agent_route is not None
        ) / max(1, len(processed))

        # Policy compliance
        policy_emails = [e for e in processed if e.policy_rules]
        policy_compliance = sum(
            self._policy_score(e) for e in policy_emails
        ) / max(1, len(policy_emails)) if policy_emails else 1.0

        avg = lambda lst: sum(lst) / len(lst)
        score = (
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
        return round(score, 4), {
            "task": "task_hard", "emails_processed": len(processed),
            "avg_routing": round(avg(routing), 4),
            "avg_urgency": round(avg(urgency), 4),
            "policy_compliance": round(policy_compliance, 4),
            "avg_sla": round(avg(sla), 4),
            "avg_reply": round(avg(replies), 4),
            "avg_tool_use": round(avg(tools), 4),
            "high_stakes_score": round(hs_score, 4),
            "chain_of_thought_score": round(cot_score, 4),
            "adversarial_handling": round(avg(adversarial), 4),
            "coverage": round(coverage, 4),
            "final_score": round(score, 4),
        }


GRADERS = {
    "task_easy":   EasyTaskGrader(),
    "task_medium": MediumTaskGrader(),
    "task_hard":   HardTaskGrader(),
}


def grade_episode(task_id: str, processed: list) -> Tuple[float, Dict]:
    if task_id not in GRADERS:
        return 0.0, {"error": f"Unknown task: {task_id}"}
    return GRADERS[task_id].grade(processed)
