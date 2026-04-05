"""
Email scenarios for all 4 inbox types.
Each email has ground truth labels, SLA timers, policy rules,
adversarial flags, and tool requirements.
"""
from __future__ import annotations
from env.models import Email, Urgency, RouteDept, PolicyRule, EmailStatus

# ── SCENARIO 1: Startup Support (task_easy, 8 emails) ────────────────────────

STARTUP_EMAILS = [
    Email(
        id="s1_001", arrival_step=0, sla_steps=15, sla_remaining=15,
        subject="Can't log in — locked out of account",
        sender="Alex Turner", sender_email="alex@mydesignco.com",
        body=(
            "Hi, I've been trying to log in for the past hour and keep getting "
            "'Invalid credentials' even after resetting my password twice. "
            "I have a client presentation in 2 hours and desperately need access. "
            "Account email: alex@mydesignco.com"
        ),
        timestamp="2024-01-15T08:00:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.SUPPORT,
        true_intent="account_lockout",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["password", "reset", "account", "access", "help", "team"],
    ),
    Email(
        id="s1_002", arrival_step=0, sla_steps=20, sla_remaining=20,
        subject="How do I export data to CSV?",
        sender="Jamie Liu", sender_email="jamie@small-biz.net",
        body=(
            "Hello! Quick question — I need to export all my records to CSV "
            "for my accountant. I looked in Settings but can't find the option. "
            "Is this available on the Starter plan?\n\nThanks, Jamie"
        ),
        timestamp="2024-01-15T08:05:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SUPPORT,
        true_intent="feature_question",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["export", "csv", "settings", "data", "plan"],
    ),
    Email(
        id="s1_003", arrival_step=0, sla_steps=10, sla_remaining=10,
        subject="Upgrade to Pro — billing question",
        sender="Sam Rivera", sender_email="sam@growthco.io",
        body=(
            "Hi team, I want to upgrade from Starter to Pro. "
            "Quick question: if I upgrade mid-month, will I be charged "
            "the full month or prorated? Also, can I use my existing "
            "payment method on file?\n\nSam"
        ),
        timestamp="2024-01-15T08:10:00Z",
        true_urgency=Urgency.MEDIUM,
        true_route=RouteDept.BILLING,
        true_intent="billing_inquiry",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["prorate", "billing", "upgrade", "payment", "charge"],
    ),
    Email(
        id="s1_004", arrival_step=0, sla_steps=8, sla_remaining=8,
        subject="URGENT: API down, breaking our production app",
        sender="Dev Team", sender_email="dev@techstartup.io",
        body=(
            "Your API has been returning 503 errors for the past 20 minutes. "
            "Our entire product is broken and we're losing customers in real time. "
            "This is a P0 for us. Ticket TKT-4421 was already opened. "
            "Need an update IMMEDIATELY.\n\nDev Team, TechStartup"
        ),
        timestamp="2024-01-15T08:15:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.ENGINEERING,
        true_intent="outage_report",
        requires_tool=True, required_tool="lookup_ticket",
        requires_reply=True,
        expected_reply_keywords=["investigating", "team", "update", "incident", "priority"],
        vip=False, financial_impact=5000.0,
    ),
    Email(
        id="s1_005", arrival_step=0, sla_steps=25, sla_remaining=25,
        subject="Feature request: dark mode",
        sender="Casey Morgan", sender_email="casey@freelancer.me",
        body=(
            "Love the product! One thing I'd really love to see is dark mode. "
            "My eyes get tired working late nights. Any plans for this? "
            "Happy to be a beta tester if needed!"
        ),
        timestamp="2024-01-15T08:20:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SALES,
        true_intent="feature_request",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["roadmap", "feature", "feedback", "consider", "thank"],
    ),
    Email(
        id="s1_006", arrival_step=2, sla_steps=12, sla_remaining=12,
        subject="Invoice #INV-2024-0044 payment failed",
        sender="Finance Bot", sender_email="billing@ourplatform.com",
        body=(
            "Automated notice: Payment for Invoice #INV-2024-0044 ($299.00) "
            "failed on January 12. Customer: sam@small-biz.net. "
            "Order: ORD-9002. Second retry scheduled for Jan 19. "
            "Please review if manual follow-up is needed."
        ),
        timestamp="2024-01-15T08:30:00Z",
        true_urgency=Urgency.MEDIUM,
        true_route=RouteDept.BILLING,
        true_intent="payment_failure",
        requires_tool=True, required_tool="lookup_order",
        requires_reply=False,
    ),
    Email(
        id="s1_007", arrival_step=3, sla_steps=30, sla_remaining=30,
        subject="Get rich quick — make $5000/day working from home!!!",
        sender="Money Guru", sender_email="guru@spam-offers.biz",
        body=(
            "AMAZING OPPORTUNITY!!! Make $5000 every single day from the comfort "
            "of your home!!! Click here NOW: http://totally-legit.biz/riches "
            "Limited spots available!!! ACT NOW!!!"
        ),
        timestamp="2024-01-15T08:35:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SUPPORT,
        true_intent="spam",
        requires_tool=False,
        requires_reply=False,
        is_adversarial=True, adversarial_type="spam",
    ),
    Email(
        id="s1_008", arrival_step=4, sla_steps=20, sla_remaining=20,
        subject="How much does the Enterprise plan cost?",
        sender="Jordan Kim", sender_email="jordan.kim@bigcorp.com",
        body=(
            "Hi, I'm evaluating your tool for my team of 200 people. "
            "I couldn't find Enterprise pricing on your website. "
            "Could you send me a quote? We'd need SSO, audit logs, "
            "and a dedicated account manager."
        ),
        timestamp="2024-01-15T08:40:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.SALES,
        true_intent="sales_inquiry",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["enterprise", "pricing", "demo", "sales", "team", "quote"],
        vip=False, financial_impact=15000.0,
    ),
]

# ── SCENARIO 2: HR Department (task_medium, 15 emails) ───────────────────────

HR_EMAILS = [
    Email(
        id="h1_001", arrival_step=0, sla_steps=8, sla_remaining=8,
        subject="Employee termination — data deletion required",
        sender="Legal Team", sender_email="legal@ourcompany.com",
        body=(
            "We have terminated employee ID EMP-4492 (John Davies) effective today. "
            "Per GDPR Article 17, we are required to delete all personal data "
            "within 30 days. Please initiate the deletion process. "
            "Ticket TKT-4601 has been opened. Do NOT auto-reply to this thread."
        ),
        timestamp="2024-01-15T09:00:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.COMPLIANCE,
        true_intent="data_deletion_request",
        requires_tool=True, required_tool="lookup_ticket",
        requires_reply=False,
        policy_rules=[PolicyRule.NO_AUTO_REPLY, PolicyRule.COMPLIANCE_REVIEW],
    ),
    Email(
        id="h1_002", arrival_step=0, sla_steps=12, sla_remaining=12,
        subject="Salary review — I deserve a raise",
        sender="Mike Thompson", sender_email="m.thompson@ourcompany.com",
        body=(
            "I have been with this company for 3 years and have not received "
            "a meaningful raise. I am being paid 20% below market rate for my role. "
            "I need this addressed within the week or I will be forced to look elsewhere. "
            "This is my formal written request."
        ),
        timestamp="2024-01-15T09:05:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.HR,
        true_intent="compensation_complaint",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["review", "schedule", "meeting", "hr", "discuss", "compensation"],
        policy_rules=[PolicyRule.HUMAN_APPROVAL],
    ),
    Email(
        id="h1_003", arrival_step=0, sla_steps=6, sla_remaining=6,
        subject="Harassment complaint — urgent and confidential",
        sender="Anonymous Employee", sender_email="anonymous@secure-report.com",
        body=(
            "I am reporting workplace harassment by my direct manager. "
            "I am filing this anonymously out of fear of retaliation. "
            "This has been ongoing for 3 months. I have documentation. "
            "I need to speak with HR immediately, NOT through my manager."
        ),
        timestamp="2024-01-15T09:10:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.HR,
        true_intent="harassment_complaint",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["confidential", "serious", "investigation", "safe", "hr", "speak"],
        policy_rules=[PolicyRule.MUST_ESCALATE, PolicyRule.HUMAN_APPROVAL, PolicyRule.NO_AUTO_REPLY],
        vip=False, financial_impact=0.0,
    ),
    Email(
        id="h1_004", arrival_step=0, sla_steps=20, sla_remaining=20,
        subject="Parental leave policy question",
        sender="Lisa Park", sender_email="l.park@ourcompany.com",
        body=(
            "Hi HR, I'm expecting in June and want to understand the parental "
            "leave policy. Specifically: how many weeks are paid, does it apply "
            "to both parents, and do I need to notify my manager before HR?\n\nThanks, Lisa"
        ),
        timestamp="2024-01-15T09:15:00Z",
        true_urgency=Urgency.MEDIUM,
        true_route=RouteDept.HR,
        true_intent="policy_question",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["parental", "leave", "weeks", "paid", "policy", "notify"],
    ),
    Email(
        id="h1_005", arrival_step=0, sla_steps=15, sla_remaining=15,
        subject="I QUIT — this place is toxic",
        sender="Angry Employee", sender_email="rage.quit@gmail.com",
        body=(
            "I cannot take this anymore. The management is incompetent, "
            "the culture is toxic, and no one listens. I am resigning effective "
            "immediately. I don't care about notice period. Good luck finding "
            "someone to replace me. You'll need it."
        ),
        timestamp="2024-01-15T09:20:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.HR,
        true_intent="resignation",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["resignation", "understand", "process", "final", "paycheck", "appreciate"],
        is_adversarial=True, adversarial_type="emotionally_charged",
        policy_rules=[PolicyRule.HUMAN_APPROVAL],
    ),
    Email(
        id="h1_006", arrival_step=1, sla_steps=18, sla_remaining=18,
        subject="Re: Re: Re: Team offsite — dates",
        sender="Project Manager", sender_email="pm@ourcompany.com",
        body=(
            "Following up again on the offsite dates thread. We still "
            "haven't heard back. The venue needs confirmation by EOD Friday "
            "or we lose the deposit ($2,000). Can someone from HR confirm "
            "Q2 blackout dates ASAP?"
        ),
        thread=[
            {"sender": "PM", "body": "Can we confirm Q2 offsite dates?", "date": "Jan 10"},
            {"sender": "HR", "body": "Looking into it, will get back to you.", "date": "Jan 11"},
            {"sender": "PM", "body": "Any update? Venue is waiting.", "date": "Jan 13"},
        ],
        timestamp="2024-01-15T09:25:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.HR,
        true_intent="scheduling_request",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["dates", "confirm", "venue", "q2", "blackout", "offsite"],
        financial_impact=2000.0,
    ),
    Email(
        id="h1_007", arrival_step=2, sla_steps=10, sla_remaining=10,
        subject="Background check authorization — new hire",
        sender="Recruiting", sender_email="recruiting@ourcompany.com",
        body=(
            "New hire Candidate ID: CAND-7821 has accepted the offer. "
            "Background check authorization is needed before start date Jan 29. "
            "Please route to compliance for review. This cannot be auto-processed."
        ),
        timestamp="2024-01-15T09:35:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.COMPLIANCE,
        true_intent="background_check",
        requires_tool=False,
        requires_reply=False,
        policy_rules=[PolicyRule.COMPLIANCE_REVIEW, PolicyRule.NO_AUTO_REPLY],
    ),
    Email(
        id="h1_008", arrival_step=2, sla_steps=25, sla_remaining=25,
        subject="Work from home equipment reimbursement",
        sender="Taylor Brown", sender_email="t.brown@ourcompany.com",
        body=(
            "Hi, I purchased a monitor ($450) and ergonomic chair ($380) "
            "for my home office setup. I have receipts for both. "
            "The total is $830. Can you process a reimbursement? "
            "My employee ID is EMP-3341."
        ),
        timestamp="2024-01-15T09:40:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.HR,
        true_intent="reimbursement_request",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["reimbursement", "receipts", "submit", "finance", "process"],
    ),
    Email(
        id="h1_009", arrival_step=3, sla_steps=8, sla_remaining=8,
        subject="Performance improvement plan — appeal",
        sender="David Chen", sender_email="d.chen@ourcompany.com",
        body=(
            "I have been placed on a PIP which I believe is unjust and retaliatory "
            "following my protected disclosure last month. I am formally appealing "
            "this decision and request an independent review. I have retained legal counsel."
        ),
        timestamp="2024-01-15T09:45:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.LEGAL,
        true_intent="legal_dispute",
        requires_tool=False,
        requires_reply=False,
        policy_rules=[PolicyRule.MUST_ESCALATE, PolicyRule.NO_AUTO_REPLY, PolicyRule.HUMAN_APPROVAL],
        vip=False, financial_impact=50000.0,
    ),
    Email(
        id="h1_010", arrival_step=3, sla_steps=20, sla_remaining=20,
        subject="Can I work from Bali for 3 months?",
        sender="Nina Osei", sender_email="n.osei@ourcompany.com",
        body=(
            "Hi! I want to ask if I can work remotely from Bali, Indonesia "
            "from March to May. I'll be in the same timezone +/- 4 hours. "
            "Is there a policy for this? Any tax implications I should know about?"
        ),
        timestamp="2024-01-15T09:50:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.HR,
        true_intent="remote_work_request",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["remote", "policy", "tax", "international", "approve", "compliance"],
        requires_clarification=True,
    ),
    Email(
        id="h1_011", arrival_step=4, sla_steps=15, sla_remaining=15,
        subject="Urgent: Medical leave starting tomorrow",
        sender="Chris Walsh", sender_email="c.walsh@ourcompany.com",
        body=(
            "I have been hospitalized and need to start medical leave immediately — "
            "tomorrow morning. I have a doctor's note. Please process emergency "
            "FMLA paperwork. My manager is unaware. Please notify them."
        ),
        timestamp="2024-01-15T09:55:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.HR,
        true_intent="medical_leave",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["fmla", "medical", "leave", "paperwork", "manager", "notify", "support"],
        policy_rules=[PolicyRule.HUMAN_APPROVAL],
    ),
    Email(
        id="h1_012", arrival_step=5, sla_steps=12, sla_remaining=12,
        subject="RE: Salary review (3rd follow-up)",
        sender="Mike Thompson", sender_email="m.thompson@ourcompany.com",
        body=(
            "This is my third email about my salary review. I still haven't "
            "received a response. I need a meeting scheduled this week or I will "
            "escalate to the CEO. I have also CC'd my union rep."
        ),
        thread=[
            {"sender": "Mike", "body": "Requesting salary review", "date": "Jan 8"},
            {"sender": "Mike", "body": "Following up — no response yet", "date": "Jan 12"},
        ],
        timestamp="2024-01-15T10:00:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.HR,
        true_intent="compensation_escalation",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["apologize", "schedule", "meeting", "review", "this week"],
        is_adversarial=True, adversarial_type="repeated_thread",
    ),
    Email(
        id="h1_013", arrival_step=6, sla_steps=30, sla_remaining=30,
        subject="Team building ideas — survey results",
        sender="Culture Committee", sender_email="culture@ourcompany.com",
        body=(
            "Hi all, here are the results from the Q1 team building survey. "
            "Top choices were: escape room (42%), cooking class (31%), volunteer day (27%). "
            "No action required from HR at this time — just FYI for planning."
        ),
        timestamp="2024-01-15T10:05:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.HR,
        true_intent="fyi_internal",
        requires_tool=False,
        requires_reply=False,
    ),
    Email(
        id="h1_014", arrival_step=7, sla_steps=10, sla_remaining=10,
        subject="I have information about financial fraud",
        sender="Concerned Employee", sender_email="whistleblower@protonmail.com",
        body=(
            "I am a current employee and I have evidence of financial fraud "
            "being committed by a senior manager. I am coming forward under "
            "the whistleblower protection policy. I cannot reveal my identity yet. "
            "How do I proceed safely?"
        ),
        timestamp="2024-01-15T10:10:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.LEGAL,
        true_intent="whistleblower_report",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["confidential", "protected", "legal", "secure", "channel", "safe"],
        policy_rules=[PolicyRule.MUST_ESCALATE, PolicyRule.NO_AUTO_REPLY, PolicyRule.HUMAN_APPROVAL],
        financial_impact=500000.0,
    ),
    Email(
        id="h1_015", arrival_step=8, sla_steps=20, sla_remaining=20,
        subject="Happy 5-year work anniversary! 🎉",
        sender="Culture Bot", sender_email="culture-bot@ourcompany.com",
        body=(
            "Congratulations to Sarah Mitchell on her 5-year work anniversary! "
            "Please remember to send her a personalized note and arrange the "
            "standard anniversary gift ($100 voucher) per company policy."
        ),
        timestamp="2024-01-15T10:15:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.HR,
        true_intent="anniversary_reminder",
        requires_tool=False,
        requires_reply=False,
    ),
]

# ── SCENARIO 3: Healthcare Admin (task_hard, 25 emails) ──────────────────────

HEALTHCARE_EMAILS = HR_EMAILS[:10] + [
    Email(
        id="hc_001", arrival_step=0, sla_steps=4, sla_remaining=4,
        subject="HIPAA data request — patient records",
        sender="Dr. Emily Ross", sender_email="emily.ross@cityhealth.org",
        body=(
            "We need an urgent export of all patient interaction logs from "
            "January 1–14. This is for an ongoing audit. Customer ID: C-1003. "
            "Ticket TKT-4502 is open. This data contains PHI — handle accordingly. "
            "Do NOT send via standard email."
        ),
        timestamp="2024-01-15T10:20:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.COMPLIANCE,
        true_intent="hipaa_data_request",
        requires_tool=True, required_tool="lookup_ticket",
        requires_reply=False,
        policy_rules=[PolicyRule.COMPLIANCE_REVIEW, PolicyRule.NO_AUTO_REPLY, PolicyRule.MUST_ESCALATE],
        vip=True, financial_impact=106800.0,
    ),
    Email(
        id="hc_002", arrival_step=0, sla_steps=6, sla_remaining=6,
        subject="System downtime impacted patient scheduling — we need SLA credit",
        sender="CityHealth IT", sender_email="it@cityhealth.org",
        body=(
            "Your platform was down for 4 hours on Jan 12 between 14:00-18:00. "
            "This directly impacted our patient scheduling system. We lost 47 appointments. "
            "Per our SLA (99.9% uptime guarantee), we are entitled to a service credit. "
            "Order ORD-9003. Please calculate and apply the credit."
        ),
        timestamp="2024-01-15T10:25:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.BILLING,
        true_intent="sla_credit_claim",
        requires_tool=True, required_tool="lookup_order",
        requires_reply=True,
        expected_reply_keywords=["sla", "credit", "downtime", "investigate", "calculate", "apply"],
        vip=True, financial_impact=106800.0,
    ),
    Email(
        id="hc_003", arrival_step=1, sla_steps=5, sla_remaining=5,
        subject="Security incident — unauthorized access attempt",
        sender="Security Team", sender_email="security@cityhealth.org",
        body=(
            "We detected 3 unauthorized access attempts on patient data portal "
            "at 03:22 AM UTC. IP: 185.234.xx.xx. We believe this may be a targeted "
            "attack. All access has been blocked. We need your security team to "
            "investigate and provide an incident report within 24 hours per our BAA."
        ),
        timestamp="2024-01-15T10:30:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.ENGINEERING,
        true_intent="security_incident",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["security", "incident", "investigate", "24 hours", "team", "breach"],
        policy_rules=[PolicyRule.MUST_ESCALATE, PolicyRule.COMPLIANCE_REVIEW],
        vip=True, financial_impact=200000.0,
    ),
    Email(
        id="hc_004", arrival_step=2, sla_steps=8, sla_remaining=8,
        subject="New feature request — HL7 FHIR integration",
        sender="Dr. Emily Ross", sender_email="emily.ross@cityhealth.org",
        body=(
            "We need HL7 FHIR R4 integration for our EHR system. "
            "This is now a regulatory requirement for us. If this isn't "
            "on your roadmap within 6 months, we may need to evaluate alternatives. "
            "Please connect us with your product team."
        ),
        timestamp="2024-01-15T10:35:00Z",
        true_urgency=Urgency.HIGH,
        true_route=RouteDept.SALES,
        true_intent="feature_request_strategic",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["fhir", "roadmap", "product", "team", "connect", "requirement"],
        vip=True, financial_impact=106800.0,
    ),
    Email(
        id="hc_005", arrival_step=3, sla_steps=4, sla_remaining=4,
        subject="Are you HIPAA compliant??? We need proof NOW",
        sender="Compliance Officer", sender_email="compliance@regional-hospital.com",
        body=(
            "Our legal team is demanding proof of your HIPAA compliance and BAA "
            "before our contract renewal next week. If we don't receive your "
            "current BAA, SOC2 Type II report, and HIPAA attestation by tomorrow, "
            "we will be terminating our contract. This is non-negotiable."
        ),
        timestamp="2024-01-15T10:40:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.LEGAL,
        true_intent="compliance_documentation_request",
        requires_tool=False,
        requires_reply=False,
        policy_rules=[PolicyRule.NO_AUTO_REPLY, PolicyRule.MUST_ESCALATE, PolicyRule.HUMAN_APPROVAL],
        financial_impact=75000.0,
    ),
    Email(
        id="hc_006", arrival_step=4, sla_steps=25, sla_remaining=25,
        subject="Monthly usage report looks wrong",
        sender="Hospital Admin", sender_email="admin@memorial-health.org",
        body=(
            "Our January usage report shows 4,200 API calls but our internal "
            "logs show only 2,800. That's a 33% discrepancy. Are we being "
            "overbilled? Please explain the difference."
        ),
        timestamp="2024-01-15T10:45:00Z",
        true_urgency=Urgency.MEDIUM,
        true_route=RouteDept.BILLING,
        true_intent="billing_discrepancy",
        requires_tool=True, required_tool="lookup_order",
        requires_reply=True,
        expected_reply_keywords=["investigate", "usage", "report", "billing", "discrepancy", "review"],
    ),
    Email(
        id="hc_007", arrival_step=5, sla_steps=3, sla_remaining=3,
        subject="CRITICAL: Database migration failing — patient data at risk",
        sender="CTO", sender_email="cto@cityhealth.org",
        body=(
            "Our scheduled database migration is failing mid-process. "
            "Patient appointment data for 1,200 patients may be corrupted. "
            "Your platform is involved in the pipeline. We need your senior "
            "engineer on a call in the next 30 minutes. This is life-critical."
        ),
        timestamp="2024-01-15T10:50:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.ENGINEERING,
        true_intent="critical_data_incident",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["engineer", "call", "immediate", "critical", "team", "30 minutes"],
        policy_rules=[PolicyRule.MUST_ESCALATE],
        vip=True, financial_impact=500000.0,
    ),
    Email(
        id="hc_008", arrival_step=6, sla_steps=20, sla_remaining=20,
        subject="Your platform is amazing — case study interest",
        sender="Marketing Coordinator", sender_email="mkt@smallclinic.com",
        body=(
            "We've been using your platform for 6 months and the results have been "
            "incredible — 40% reduction in admin time. We'd love to be featured "
            "in a case study. Who should we talk to about this?"
        ),
        timestamp="2024-01-15T10:55:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SALES,
        true_intent="marketing_opportunity",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["case study", "marketing", "team", "connect", "success", "thank"],
    ),
    Email(
        id="hc_009", arrival_step=7, sla_steps=5, sla_remaining=5,
        subject="Contract renewal — we're considering leaving",
        sender="Priya Nair", sender_email="priya@techgiant.com",
        body=(
            "Our annual contract (ORD-9004) is up for renewal in 14 days. "
            "We've had 5 open tickets (including TKT-4489) unresolved for weeks. "
            "We're actively evaluating your two main competitors. "
            "We need a call with your VP of Customer Success this week or "
            "we will not be renewing."
        ),
        timestamp="2024-01-15T11:00:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.EXECUTIVE,
        true_intent="churn_risk",
        requires_tool=True, required_tool="lookup_order",
        requires_reply=True,
        expected_reply_keywords=["vp", "call", "this week", "resolve", "priority", "renewal", "apologize"],
        policy_rules=[PolicyRule.MUST_ESCALATE],
        vip=True, financial_impact=180000.0,
    ),
    Email(
        id="hc_010", arrival_step=8, sla_steps=15, sla_remaining=15,
        subject="Completely satisfied — just wanted to say thanks",
        sender="Dr. Marcus Webb", sender_email="m.webb@family-practice.com",
        body=(
            "Hi! Just wanted to drop a note to say your support team has been "
            "absolutely fantastic. Specifically, the rep who helped me last week "
            "went above and beyond. Please pass this along to their manager. "
            "Happy customer here!"
        ),
        timestamp="2024-01-15T11:05:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SUPPORT,
        true_intent="positive_feedback",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["thank", "appreciate", "share", "team", "feedback"],
    ),
    Email(
        id="hc_011", arrival_step=9, sla_steps=5, sla_remaining=5,
        subject="This is definitely not a phishing email",
        sender="IT Security", sender_email="it-security@0urcompany.com",
        body=(
            "IMPORTANT: Your password expires in 24 hours. Click here immediately "
            "to reset: http://0urcompany.com/reset-now. "
            "Failure to reset will lock your account permanently. Act NOW."
        ),
        timestamp="2024-01-15T11:10:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SUPPORT,
        true_intent="phishing_attempt",
        requires_tool=False,
        requires_reply=False,
        is_adversarial=True, adversarial_type="phishing",
    ),
    Email(
        id="hc_012", arrival_step=10, sla_steps=6, sla_remaining=6,
        subject="???",
        sender="Unknown", sender_email="noreply@no-domain.invalid",
        body=".",
        timestamp="2024-01-15T11:15:00Z",
        true_urgency=Urgency.LOW,
        true_route=RouteDept.SUPPORT,
        true_intent="incomplete_spam",
        requires_tool=False,
        requires_reply=False,
        is_adversarial=True, adversarial_type="incomplete_thread",
    ),
    Email(
        id="hc_013", arrival_step=11, sla_steps=4, sla_remaining=4,
        subject="Data breach — you must notify all affected patients NOW",
        sender="Lawyer", sender_email="attorney@legal-threats.com",
        body=(
            "On behalf of our clients, we are formally notifying you of a "
            "potential class action lawsuit related to the alleged data breach "
            "affecting patient records. You are required by HIPAA to notify all "
            "affected individuals within 60 days. Failure to comply will result in "
            "regulatory fines of up to $1.9M per violation. Do not ignore this."
        ),
        timestamp="2024-01-15T11:20:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.LEGAL,
        true_intent="legal_threat",
        requires_tool=False,
        requires_reply=False,
        policy_rules=[PolicyRule.NO_AUTO_REPLY, PolicyRule.MUST_ESCALATE, PolicyRule.HUMAN_APPROVAL],
        financial_impact=1900000.0,
    ),
    Email(
        id="hc_014", arrival_step=12, sla_steps=15, sla_remaining=15,
        subject="API documentation is outdated — v3 endpoints missing",
        sender="Integration Dev", sender_email="dev@medtech-startup.io",
        body=(
            "Your API docs still show v2 endpoints but your changelog mentions v3. "
            "The new /patients/records endpoint is completely undocumented. "
            "We're building a production integration and can't proceed without "
            "the correct specs. Can you point us to the right docs?"
        ),
        timestamp="2024-01-15T11:25:00Z",
        true_urgency=Urgency.MEDIUM,
        true_route=RouteDept.ENGINEERING,
        true_intent="documentation_request",
        requires_tool=False,
        requires_reply=True,
        expected_reply_keywords=["documentation", "v3", "api", "specs", "link", "team"],
    ),
    Email(
        id="hc_015", arrival_step=13, sla_steps=3, sla_remaining=3,
        subject="LAST WARNING before legal action",
        sender="Angry Former Customer", sender_email="former@angry-client.com",
        body=(
            "I have sent 8 emails and called 4 times. Nobody responds. "
            "I was overcharged $4,200 and still haven't received my refund "
            "that was promised 3 months ago. I am filing complaints with the "
            "FTC, BBB, and my state attorney general TODAY unless I hear back "
            "within 2 hours. This is your FINAL warning."
        ),
        timestamp="2024-01-15T11:30:00Z",
        true_urgency=Urgency.CRITICAL,
        true_route=RouteDept.LEGAL,
        true_intent="legal_escalation",
        requires_tool=True, required_tool="lookup_customer",
        requires_reply=True,
        expected_reply_keywords=["apologize", "refund", "resolve", "immediate", "call", "today"],
        policy_rules=[PolicyRule.MUST_ESCALATE, PolicyRule.HUMAN_APPROVAL],
        is_adversarial=True, adversarial_type="emotionally_charged",
        financial_impact=4200.0,
    ),
]

SCENARIO_EMAILS = {
    "task_easy":   STARTUP_EMAILS,
    "task_medium": HR_EMAILS,
    "task_hard":   HEALTHCARE_EMAILS,
}

SCENARIO_NAMES = {
    "task_easy":   "startup_support",
    "task_medium": "hr_department",
    "task_hard":   "healthcare_admin",
}
