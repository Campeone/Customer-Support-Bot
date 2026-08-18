import os
import json
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from query_engine import query
from router import route

load_dotenv()

# ── App setup ────────────────────────────────────────────────────
app = FastAPI(
    title="ShopEase Customer Support API",
    description="RAG-powered customer support bot for ShopEase",
    version="1.0.0"
)

# Allow requests from the Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Request & Response models ─────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"      # Optional — for tracking in production

class ChatResponse(BaseModel):
    message: str
    confidence: float
    escalated: bool
    sources: list
    ticket_id: str | None = None    # Only present if escalated
    assigned_to: str | None = None  # Only present if escalated

# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "ShopEase Support Bot",
        "version": "1.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.
    1. Runs RAG query against the knowledge base
    2. If confident -> returns AI answer directly
    3. If not confident -> escalates to human agent and returns ticket info
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Step 1: Run RAG query
        rag_result = query(request.message)

        answer = rag_result["answer"]
        confidence = rag_result["confidence"]
        escalate = rag_result["escalate"]
        sources = rag_result["sources"]

        # Step 2: Handle escalation
        if escalate:
            routing = route(request.message, answer, confidence)
            return ChatResponse(
                message=routing["escalation_message"],
                confidence=confidence,
                escalated=True,
                sources=sources,
                ticket_id=routing["ticket_id"],
                assigned_to=routing["assigned_to"]
            )

        # Step 3: Return AI answer directly
        return ChatResponse(
            message=answer,
            confidence=confidence,
            escalated=False,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tickets")
def get_tickets():
    """
    Returns all escalated support tickets.
    In production this would query Zendesk or your CRM.
    """
    tickets_dir = os.path.join(os.path.dirname(__file__), "..", "tickets")

    if not os.path.exists(tickets_dir):
        return {"tickets": [], "total": 0}

    tickets = []
    for filename in os.listdir(tickets_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(tickets_dir, filename)
            with open(filepath, "r") as f:
                tickets.append(json.load(f))

    # Sort by created_at, newest first
    tickets.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "tickets": tickets,
        "total": len(tickets)
    }