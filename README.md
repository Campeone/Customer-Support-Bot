# ShopEase AI Customer Support Bot

A RAG-powered customer support chatbot that automatically answers 75%+ of 
customer queries 24/7 — with intelligent escalation routing to human agents 
for complex issues.

Live demo: https://customer-support-bot-jmjte86ddprbl4tnl4jfgg.streamlit.app/

---

## The Business Problem

Most e-commerce companies have support agents spending 80% of their time 
answering the same questions repeatedly:

- "Where is my order?"
- "What is your return policy?"
- "How do I track my shipment?"

This system automates those repetitive queries instantly, 24/7, and only 
escalates genuinely complex issues to human agents — freeing your team to 
focus on work that actually needs a human.

---

## How It Works

```text
User sends a question
        │
        ▼
Question is embedded into a vector
        │
        ▼
ChromaDB finds the 3 most relevant knowledge base chunks
        │
        ▼
GPT-4o-mini generates a grounded answer from retrieved context
        │
   ┌────┴────┐
confident    not confident
        │            │
        ▼            ▼
Answer returned   Ticket created
to user           and routed to
                  right human team
```
--- 

## Features

- **RAG pipeline** — answers are grounded in company documents, not hallucinated
- **Confidence scoring** — every answer is scored; low confidence triggers escalation
- **Intelligent routing** — escalated queries are assigned to the right specialist team (billing, returns, shipping, etc.)
- **Ticket system** — every escalation generates a structured support ticket with full context
- **Source transparency** — UI shows which document each answer came from
- **Session analytics** — real-time automation rate tracked in the sidebar
- **REST API** — full FastAPI backend with `/chat`, `/health`, and `/tickets` endpoints

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | GPT-4o-mini (OpenAI) |
| Embeddings | text-embedding-3-small (OpenAI) |
| RAG orchestration | LlamaIndex |
| Vector database | ChromaDB |
| Backend API | FastAPI |
| Frontend | Streamlit |
| Deployment | Hugging Face Spaces (Docker) |

---

## Project Structure

```text
customer-support-bot/
│
├── app.py                        # Streamlit chat UI
├── Dockerfile                    # Container definition
├── start.sh                      # Startup script
├── requirements.txt
│
├── backend/
│   ├── ingest.py                 # Document ingestion pipeline
│   ├── query_engine.py           # RAG logic + confidence scoring
│   ├── router.py                 # Escalation routing + ticket creation
│   └── main.py                   # FastAPI REST API
│
└── data/                         # Company knowledge base
    ├── faqs.txt
    ├── return_policy.txt
    ├── shipping_info.txt
    ├── product_catalog.txt
    ├── order_management.txt
    ├── complaints_and_escalations.txt
    └── account_and_general.txt
```

---

## Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/Campeone/Customer-Support-Bot.git
cd customer-support-bot
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### 5. Run ingestion
```bash
python backend/ingest.py
```

### 6. Start the app
```bash
streamlit run app.py
```

Visit `http://localhost:8501`

---

## Running with Docker

```bash
docker build -t shopease-bot .
docker run -p 7860:7860 -e OPENAI_API_KEY=your-key-here shopease-bot
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Check API status |
| POST | `/chat` | Send a message, get AI response |
| GET | `/tickets` | View all escalated support tickets |

### Example request
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your return policy?"}'
```

### Example response
```json
{
  "message": "You have 30 days from delivery to return most items...",
  "confidence": 0.82,
  "escalated": false,
  "sources": ["return_policy.txt"],
  "ticket_id": null,
  "assigned_to": null
}
```

---

## Key AI Engineering Concepts Demonstrated

- **Retrieval-Augmented Generation (RAG)** — grounding LLM responses in private documents
- **Vector embeddings** — semantic search beyond simple keyword matching
- **Confidence scoring** — threshold-based routing for reliable automation
- **Prompt engineering** — custom system prompt prevents hallucination
- **Chunking strategy** — optimal document splitting for precise retrieval
- **Production API design** — Pydantic validation, error handling, CORS

---

## Extending This Project

This system is designed to be easily extended for real clients:

- **Swap the knowledge base** — replace `data/` with any company's documents
- **Connect a real ticketing system** — replace JSON files with Zendesk or Freshdesk API calls
- **Add order lookup** — connect `query_engine.py` to a live order management API
- **Scale the vector DB** — swap ChromaDB for Pinecone for production scale
- **Add authentication** — protect the API with JWT tokens

---

## License

MIT License — free to use and adapt for your own projects.
```

---

Also create a `.env.example` file so anyone cloning the repo knows what's needed:

```bash
# .env.example
OPENAI_API_KEY=your-openai-api-key-here
```

---

## Push everything to GitHub

```bash
git add .
git commit -m "Add README and .env.example"
git push origin main
```

---

