import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Add backend to path so we can import directly
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from query_engine import query
from router import route

load_dotenv()

# ── Page setup ───────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopEase Support",
    page_icon="Shopping Bags",
    layout="centered"
)

# ── Custom CSS ────────────────────────────────────────────────────
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        }
        .confidence-bar {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
        .escalated-badge {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 10px;
            margin-top: 8px;
            font-size: 13px;
        }
        .source-badge {
            background-color: #e8f4f8;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
            color: #0077b6;
            margin-right: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────
st.markdown("""
    <div class="chat-header">
        <h2>ShopEase Customer Support</h2>
        <p>Hi! I am your AI support assistant. Ask me anything about
        orders, returns, shipping, or our products.</p>
    </div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Helper — process a message ────────────────────────────────────
def process_message(user_input: str) -> dict:
    """
    Calls backend functions directly — no HTTP needed.
    Returns a unified response dict.
    """
    rag_result = query(user_input)

    answer = rag_result["answer"]
    confidence = rag_result["confidence"]
    escalate = rag_result["escalate"]
    sources = rag_result["sources"]

    if escalate:
        routing = route(user_input, answer, confidence)
        return {
            "message": routing["escalation_message"],
            "confidence": confidence,
            "escalated": True,
            "sources": sources,
            "ticket_id": routing["ticket_id"],
            "assigned_to": routing["assigned_to"]
        }

    return {
        "message": answer,
        "confidence": confidence,
        "escalated": False,
        "sources": sources,
        "ticket_id": None,
        "assigned_to": None
    }

# ── Helper — render assistant metadata ────────────────────────────
def render_meta(meta: dict):
    confidence_pct = int(meta["confidence"] * 100)
    confidence_color = (
        "green" if confidence_pct >= 40
        else "orange" if confidence_pct >= 25
        else "red"
    )
    st.markdown(
        f'<div class="confidence-bar">'
        f'Confidence: <span style="color:{confidence_color}">'
        f'{confidence_pct}%</span></div>',
        unsafe_allow_html=True
    )

    if meta.get("sources"):
        sources_html = " ".join([
            f'<span class="source-badge">{s}</span>'
            for s in meta["sources"]
        ])
        st.markdown(
            f'<div style="margin-top:4px">{sources_html}</div>',
            unsafe_allow_html=True
        )

    if meta.get("escalated"):
        st.markdown(
            f'<div class="escalated-badge">'
            f'Ticket raised: <strong>{meta["ticket_id"]}</strong>'
            f' &nbsp;|&nbsp; '
            f'Assigned to: <strong>{meta["assigned_to"]}</strong>'
            f'</div>',
            unsafe_allow_html=True
        )

# ── Render chat history ───────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            render_meta(msg["meta"])

# ── Suggested questions ───────────────────────────────────────────
if len(st.session_state.messages) == 0:
    st.markdown("**Suggested questions:**")
    suggestions = [
        "What is your return policy?",
        "How do I track my order?",
        "What payment methods do you accept?",
        "How long does shipping take?",
        "My item arrived damaged, what do I do?",
    ]
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        if cols[i % 2].button(suggestion, use_container_width=True):
            st.session_state.pending_message = suggestion
            st.rerun()

# ── Handle pending message from button click ──────────────────────
if "pending_message" in st.session_state:
    user_input = st.session_state.pop("pending_message")
else:
    user_input = None

# ── Chat input ────────────────────────────────────────────────────
typed_input = st.chat_input("Type your question here...")
if typed_input:
    user_input = typed_input

# ── Process message ───────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                data = process_message(user_input)

                st.markdown(data["message"])
                render_meta({
                    "confidence": data["confidence"],
                    "sources": data.get("sources", []),
                    "escalated": data.get("escalated", False),
                    "ticket_id": data.get("ticket_id"),
                    "assigned_to": data.get("assigned_to")
                })

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["message"],
                    "meta": {
                        "confidence": data["confidence"],
                        "sources": data.get("sources", []),
                        "escalated": data.get("escalated", False),
                        "ticket_id": data.get("ticket_id"),
                        "assigned_to": data.get("assigned_to")
                    }
                })

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ShopEase Support Bot")
    st.markdown("---")

    # Session stats
    user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
    escalated = len([
        m for m in st.session_state.messages
        if m["role"] == "assistant" and m.get("meta", {}).get("escalated")
    ])
    automated = user_msgs - escalated

    st.markdown("### Session Stats")
    st.metric("Questions Asked", user_msgs)
    st.metric("Answered by AI", automated)
    st.metric("Escalated to Human", escalated)

    if user_msgs > 0:
        automation_rate = int((automated / user_msgs) * 100)
        st.metric("Automation Rate", f"{automation_rate}%")

    st.markdown("---")

    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Tickets viewer
    st.markdown("---")
    st.markdown("### Support Tickets")
    if st.button("Load Tickets", use_container_width=True):
        tickets_dir = os.path.join(
            os.path.dirname(__file__), "tickets"
        )
        if not os.path.exists(tickets_dir):
            st.info("No tickets yet.")
        else:
            import json
            ticket_files = [
                f for f in os.listdir(tickets_dir)
                if f.endswith(".json")
            ]
            if not ticket_files:
                st.info("No tickets yet.")
            else:
                st.markdown(f"**{len(ticket_files)} ticket(s):**")
                for filename in sorted(ticket_files, reverse=True):
                    filepath = os.path.join(tickets_dir, filename)
                    with open(filepath) as f:
                        ticket = json.load(f)
                    with st.expander(
                        f"{ticket['ticket_id']} - {ticket['priority'].upper()}"
                    ):
                        st.write(f"**Assigned to:** {ticket['assigned_to']}")
                        st.write(f"**Customer asked:** {ticket['customer_message']}")
                        st.write(f"**Status:** {ticket['status']}")
                        st.write(f"**Created:** {ticket['created_at']}")