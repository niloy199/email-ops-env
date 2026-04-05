"""
Typed Pydantic models for Email Operations Center OpenEnv v2.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    SELECT_EMAIL          = "select_email"
    EXTRACT_INTENT        = "extract_intent"
    LOOKUP_CUSTOMER       = "lookup_customer"
    LOOKUP_TICKET         = "lookup_ticket"
    LOOKUP_ORDER          = "lookup_order"
    REPLY                 = "reply"
    ESCALATE              = "escalate"
    ROUTE                 = "route"
    SCHEDULE_FOLLOWUP     = "schedule_followup"
    REQUEST_CLARIFICATION = "request_clarification"
    ARCHIVE               = "archive"
    FLAG_POLICY_VIOLATION = "flag_policy_violation"
    DELETE                = "delete"


class Urgency(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class RouteDept(str, Enum):
    SUPPORT     = "support"
    BILLING     = "billing"
    LEGAL       = "legal"
    ENGINEERING = "engineering"
    SALES       = "sales"
    HR          = "hr"
    COMPLIANCE  = "compliance"
    EXECUTIVE   = "executive"


class EmailStatus(str, Enum):
    PENDING   = "pending"
    SELECTED  = "selected"
    WORKING   = "working"
    COMPLETED = "completed"
    BREACHED  = "breached"


class PolicyRule(str, Enum):
    MUST_ESCALATE        = "must_escalate"
    NO_AUTO_REPLY        = "no_auto_reply"
    REQUIRES_TOOL_LOOKUP = "requires_tool_lookup"
    HUMAN_APPROVAL       = "human_approval"
    COMPLIANCE_REVIEW    = "compliance_review"


class Email(BaseModel):
    id: str
    subject: str
    sender: str
    sender_email: str
    body: str
    thread: List[Dict[str, str]] = Field(default_factory=list)
    timestamp: str
    arrival_step: int = 0
    sla_steps: int = 10
    sla_remaining: int = 10
    status: EmailStatus = EmailStatus.PENDING
    vip: bool = False
    financial_impact: float = 0.0

    # Ground truth for grading
    true_urgency: Optional[Urgency] = None
    true_route: Optional[RouteDept] = None
    true_intent: Optional[str] = None
    requires_tool: bool = False
    required_tool: Optional[str] = None
    policy_rules: List[PolicyRule] = Field(default_factory=list)
    is_adversarial: bool = False
    adversarial_type: Optional[str] = None
    requires_reply: bool = False
    expected_reply_keywords: List[str] = Field(default_factory=list)
    requires_clarification: bool = False

    # Agent actions
    agent_intent: Optional[str] = None
    agent_urgency: Optional[Urgency] = None
    agent_route: Optional[RouteDept] = None
    agent_reply: Optional[str] = None
    agent_action: Optional[ActionType] = None
    tool_was_called: bool = False
    policy_flagged: bool = False
    sla_breached: bool = False
    steps_taken: int = 0


class ToolResult(BaseModel):
    tool: str
    query_id: str
    found: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class Observation(BaseModel):
    inbox: List[Email]
    processed: List[Email]
    current_email: Optional[Email] = None
    tool_results: Optional[ToolResult] = None
    step_count: int = 0
    inbox_size: int = 0
    sla_breached: List[str] = Field(default_factory=list)
    pending_arrivals: int = 0
    scenario: str = ""
    done: bool = False
    task_id: str = ""
    message: str = ""


class Action(BaseModel):
    action_type: ActionType
    email_id: Optional[str] = None
    intent: Optional[str] = None
    urgency: Optional[Urgency] = None
    entities: List[str] = Field(default_factory=list)
    lookup_id: Optional[str] = None
    route_to: Optional[RouteDept] = None
    reply_text: Optional[str] = None
    reason: Optional[str] = None
    followup_hours: Optional[int] = None


class Reward(BaseModel):
    value: float = Field(ge=-1.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    message: str = ""


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetRequest(BaseModel):
    task_id: str = "task_easy"
    seed: Optional[int] = None


class TaskInfo(BaseModel):
    id: str
    name: str
    difficulty: str
    description: str
    num_emails: int
    max_steps: int
    scenario: str
