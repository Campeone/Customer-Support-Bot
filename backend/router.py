import os
import json
import uuid
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────────
TICKETS_DIR = os.path.join(os.path.dirname(__file__), "..", "tickets")

# Agent routing rules — maps query keywords to specialist agents
AGENT_ROUTING_RULES = {
    "order": {
        "agent": "Order Management Team",
        "email": "orders@shopease.com",
        "priority": "high"
    },
    "return": {
        "agent": "Returns & Refunds Team",
        "email": "returns@shopease.com",
        "priority": "medium"
    },
    "refund": {
        "agent": "Returns & Refunds Team",
        "email": "returns@shopease.com",
        "priority": "medium"
    },
    "payment": {
        "agent": "Billing Team",
        "email": "billing@shopease.com",
        "priority": "high"
    },
    "damaged": {
        "agent": "Quality & Complaints Team",
        "email": "quality@shopease.com",
        "priority": "urgent"
    },
    "defective": {
        "agent": "Quality & Complaints Team",
        "email": "quality@shopease.com",
        "priority": "urgent"
    },
    "shipping": {
        "agent": "Shipping & Logistics Team",
        "email": "shipping@shopease.com",
        "priority": "medium"
    },
    "account": {
        "agent": "Account Support Team",
        "email": "accounts@shopease.com",
        "priority": "low"
    },
}

DEFAULT_AGENT = {
    "agent": "General Support Team",
    "email": "support@shopease.com",
    "priority": "medium"
}

# ── Step 1: Determine which agent to route to ────────────────────
def determine_agent(user_message: str) -> dict:
    """
    Scans the user message for keywords and routes
    to the most relevant specialist agent.
    """
    message_lower = user_message.lower()

    for keyword, agent_info in AGENT_ROUTING_RULES.items():
        if keyword in message_lower:
            return agent_info

    return DEFAULT_AGENT

# ── Step 2: Create a support ticket ─────────────────────────────
def create_ticket(user_message: str, ai_answer: str, confidence: float) -> dict:
    """
    Creates a structured support ticket and saves it to disk.
    In production this would call a ticketing API (Zendesk, Freshdesk etc.)
    """
    # Make sure tickets folder exists
    os.makedirs(TICKETS_DIR, exist_ok=True)

    agent_info = determine_agent(user_message)

    ticket = {
        "ticket_id": f"TICKET-{str(uuid.uuid4())[:8].upper()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "open",
        "priority": agent_info["priority"],
        "assigned_to": agent_info["agent"],
        "assigned_email": agent_info["email"],
        "customer_message": user_message,
        "ai_attempted_answer": ai_answer,
        "ai_confidence_score": confidence,
        "escalation_reason": (
            "Low confidence score" if confidence < 0.25
            else "AI admitted insufficient knowledge"
        )
    }

    # Save ticket as JSON file
    ticket_path = os.path.join(TICKETS_DIR, f"{ticket['ticket_id']}.json")
    with open(ticket_path, "w") as f:
        json.dump(ticket, f, indent=2)

    return ticket

# ── Step 3: Main router function ─────────────────────────────────
def route(user_message: str, ai_answer: str, confidence: float) -> dict:
    """
    Main function called by the API when escalate=True.
    Returns routing decision and ticket details.
    """
    ticket = create_ticket(user_message, ai_answer, confidence)

    # Build the customer-facing escalation message
    escalation_message = (
        f"I've escalated your question to our {ticket['assigned_to']}. "
        f"They will reach out to you at your registered email address shortly. "
        f"Your support ticket ID is {ticket['ticket_id']}. "
        f"You can also reach them directly at {ticket['assigned_email']}."
    )

    return {
        "ticket_id": ticket["ticket_id"],
        "assigned_to": ticket["assigned_to"],
        "assigned_email": ticket["assigned_email"],
        "priority": ticket["priority"],
        "escalation_message": escalation_message
    }

# ── Quick test ────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        {
            "message": "I want to return a damaged item I received",
            "answer": "I don't have enough information to answer that.",
            "confidence": 0.18
        },
        {
            "message": "My payment was charged twice",
            "answer": "I don't have enough information to answer that.",
            "confidence": 0.21
        },
        {
            "message": "Do you sell motorcycles?",
            "answer": "I don't have enough information to answer that.",
            "confidence": 0.20
        },
    ]

    print("\n[TEST] Running router tests...\n")
    print("=" * 60)

    for case in test_cases:
        print(f"\nCustomer message : {case['message']}")
        result = route(case["message"], case["answer"], case["confidence"])
        print(f"Ticket ID        : {result['ticket_id']}")
        print(f"Assigned to      : {result['assigned_to']}")
        print(f"Priority         : {result['priority']}")
        print(f"Escalation msg   : {result['escalation_message']}")
        print("-" * 60)