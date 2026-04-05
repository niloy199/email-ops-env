"""
Mock tool system: CRM, ticket DB, and order system.
Agent calls these before deciding action — rewarded for relevant lookups.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from env.models import ToolResult

# ── Mock CRM Database ─────────────────────────────────────────────────────────

CUSTOMERS: Dict[str, Dict] = {
    "C-1001": {
        "name": "Sarah Chen", "email": "sarah.chen@acmecorp.com",
        "plan": "Enterprise", "mrr": 4200, "since": "2021-03-15",
        "open_tickets": 2, "churn_risk": "low", "vip": True,
        "notes": "Key account. Direct line to VP Sales.",
    },
    "C-1002": {
        "name": "Bob Martinez", "email": "bob.m@startup.io",
        "plan": "Pro", "mrr": 299, "since": "2023-09-01",
        "open_tickets": 0, "churn_risk": "medium", "vip": False,
        "notes": "Mentioned competitor in last survey.",
    },
    "C-1003": {
        "name": "Dr. Emily Ross", "email": "emily.ross@cityhealth.org",
        "plan": "Healthcare", "mrr": 8900, "since": "2020-01-10",
        "open_tickets": 1, "churn_risk": "low", "vip": True,
        "notes": "HIPAA compliance required. Legal must review all data requests.",
    },
    "C-1004": {
        "name": "James Okafor", "email": "j.okafor@lawfirm.com",
        "plan": "Legal", "mrr": 1200, "since": "2022-06-22",
        "open_tickets": 0, "churn_risk": "low", "vip": False,
        "notes": "All communications require legal review before auto-reply.",
    },
    "C-1005": {
        "name": "Priya Nair", "email": "priya@techgiant.com",
        "plan": "Enterprise+", "mrr": 15000, "since": "2019-11-01",
        "open_tickets": 5, "churn_risk": "high", "vip": True,
        "notes": "URGENT: At-risk account. Escalate any issues to executive team.",
    },
    "C-1006": {
        "name": "Unknown", "email": "anonymous@tempmail.xyz",
        "plan": "Free", "mrr": 0, "since": "2024-01-01",
        "open_tickets": 12, "churn_risk": "high", "vip": False,
        "notes": "Flagged for abuse — 12 tickets in 30 days.",
    },
    "C-1007": {
        "name": "Maria Santos", "email": "m.santos@university.edu",
        "plan": "Education", "mrr": 500, "since": "2022-08-15",
        "open_tickets": 0, "churn_risk": "low", "vip": False,
        "notes": "University account — bulk license.",
    },
    "C-1008": {
        "name": "HR Department", "email": "hr@ourcompany.com",
        "plan": "Internal", "mrr": 0, "since": "2018-01-01",
        "open_tickets": 3, "churn_risk": "none", "vip": False,
        "notes": "Internal HR. All employee data requests need compliance sign-off.",
    },
}

# ── Mock Ticket Database ───────────────────────────────────────────────────────

TICKETS: Dict[str, Dict] = {
    "TKT-4421": {
        "title": "API returning 500 errors on /v2/process",
        "status": "open", "priority": "high",
        "created": "2024-01-14", "customer_id": "C-1001",
        "assigned_to": "engineering", "last_update": "8 hours ago",
        "notes": "Suspected memory leak in worker process. Patch in progress.",
    },
    "TKT-4398": {
        "title": "Invoice dispute — overcharged Q4",
        "status": "pending", "priority": "medium",
        "created": "2024-01-10", "customer_id": "C-1002",
        "assigned_to": "billing", "last_update": "3 days ago",
        "notes": "Awaiting finance sign-off on $450 credit.",
    },
    "TKT-4502": {
        "title": "HIPAA data export request",
        "status": "blocked", "priority": "critical",
        "created": "2024-01-15", "customer_id": "C-1003",
        "assigned_to": "compliance", "last_update": "1 hour ago",
        "notes": "Legal review required before any data is released.",
    },
    "TKT-4489": {
        "title": "SSO integration not working with Okta",
        "status": "open", "priority": "high",
        "created": "2024-01-13", "customer_id": "C-1005",
        "assigned_to": "engineering", "last_update": "2 days ago",
        "notes": "At-risk account. Fast-track this.",
    },
    "TKT-4310": {
        "title": "Bulk spam complaints from free tier user",
        "status": "flagged", "priority": "low",
        "created": "2024-01-01", "customer_id": "C-1006",
        "assigned_to": "trust_safety", "last_update": "5 days ago",
        "notes": "Under review for ToS violation.",
    },
    "TKT-4601": {
        "title": "Employee termination data deletion request",
        "status": "open", "priority": "high",
        "created": "2024-01-15", "customer_id": "C-1008",
        "assigned_to": "compliance", "last_update": "30 min ago",
        "notes": "GDPR/CCPA applies. Compliance must approve before deletion.",
    },
}

# ── Mock Order Database ────────────────────────────────────────────────────────

ORDERS: Dict[str, Dict] = {
    "ORD-9001": {
        "product": "Enterprise Plan — Annual",
        "amount": 50400.0, "currency": "USD",
        "status": "active", "customer_id": "C-1001",
        "start_date": "2024-01-01", "end_date": "2024-12-31",
        "payment_status": "paid", "invoice": "INV-2024-0001",
    },
    "ORD-9002": {
        "product": "Pro Plan — Monthly",
        "amount": 299.0, "currency": "USD",
        "status": "active", "customer_id": "C-1002",
        "start_date": "2024-01-01", "end_date": "2024-01-31",
        "payment_status": "failed", "invoice": "INV-2024-0044",
        "notes": "Payment failed on Jan 12. Second retry pending.",
    },
    "ORD-9003": {
        "product": "Healthcare Plan — Annual",
        "amount": 106800.0, "currency": "USD",
        "status": "active", "customer_id": "C-1003",
        "start_date": "2024-01-01", "end_date": "2024-12-31",
        "payment_status": "paid", "invoice": "INV-2024-0002",
    },
    "ORD-9004": {
        "product": "Enterprise+ Plan — Annual",
        "amount": 180000.0, "currency": "USD",
        "status": "renewal_due", "customer_id": "C-1005",
        "start_date": "2023-11-01", "end_date": "2024-01-31",
        "payment_status": "pending", "invoice": "INV-2024-0098",
        "notes": "Renewal at risk. 14 days to expiry.",
    },
}

# ── Tool Functions ─────────────────────────────────────────────────────────────

def lookup_customer(query_id: str) -> ToolResult:
    """Look up customer by ID or email."""
    # Try direct ID lookup
    if query_id in CUSTOMERS:
        return ToolResult(
            tool="crm", query_id=query_id, found=True,
            data=CUSTOMERS[query_id],
            message=f"Customer found: {CUSTOMERS[query_id]['name']}",
        )
    # Try email lookup
    for cid, cdata in CUSTOMERS.items():
        if cdata["email"].lower() == query_id.lower():
            return ToolResult(
                tool="crm", query_id=query_id, found=True,
                data={**cdata, "id": cid},
                message=f"Customer found by email: {cdata['name']}",
            )
    return ToolResult(
        tool="crm", query_id=query_id, found=False,
        message=f"No customer found for: {query_id}",
    )


def lookup_ticket(query_id: str) -> ToolResult:
    """Look up support ticket by ID."""
    if query_id in TICKETS:
        return ToolResult(
            tool="tickets", query_id=query_id, found=True,
            data=TICKETS[query_id],
            message=f"Ticket found: {TICKETS[query_id]['title']}",
        )
    # Fuzzy: find tickets for a customer
    customer_tickets = {
        tid: t for tid, t in TICKETS.items()
        if t.get("customer_id") == query_id
    }
    if customer_tickets:
        return ToolResult(
            tool="tickets", query_id=query_id, found=True,
            data={"tickets": customer_tickets},
            message=f"Found {len(customer_tickets)} ticket(s) for customer {query_id}",
        )
    return ToolResult(
        tool="tickets", query_id=query_id, found=False,
        message=f"No ticket found for: {query_id}",
    )


def lookup_order(query_id: str) -> ToolResult:
    """Look up order by ID."""
    if query_id in ORDERS:
        return ToolResult(
            tool="orders", query_id=query_id, found=True,
            data=ORDERS[query_id],
            message=f"Order found: {ORDERS[query_id]['product']}",
        )
    customer_orders = {
        oid: o for oid, o in ORDERS.items()
        if o.get("customer_id") == query_id
    }
    if customer_orders:
        return ToolResult(
            tool="orders", query_id=query_id, found=True,
            data={"orders": customer_orders},
            message=f"Found {len(customer_orders)} order(s) for customer {query_id}",
        )
    return ToolResult(
        tool="orders", query_id=query_id, found=False,
        message=f"No order found for: {query_id}",
    )


TOOL_DISPATCH = {
    "lookup_customer": lookup_customer,
    "lookup_ticket":   lookup_ticket,
    "lookup_order":    lookup_order,
}
