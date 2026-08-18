import os
from dotenv import load_dotenv

import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings


load_dotenv()

# ── Configuration ────────────────────────────────────────────────
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "shopease_support"

# Confidence threshold — below this score, route to human
CONFIDENCE_THRESHOLD = 0.25

# ── Custom prompt — keeps answers grounded in docs ───────────────
SUPPORT_PROMPT = PromptTemplate(
    "You are a helpful customer support assistant for ShopEase, "
    "an online retail store.\n\n"
    "Use ONLY the context below to answer the customer's question. "
    "Be friendly, concise, and professional.\n\n"
    "If the answer is not found in the context, say exactly: "
    "'I don't have enough information to answer that. "
    "Let me connect you with a human agent who can help.'\n\n"
    "Context:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n\n"
    "Customer question: {query_str}\n\n"
    "Answer:"
)

# ── Step 1: Configure LlamaIndex settings ────────────────────────
def configure_settings():
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.2       # Low temperature = consistent, factual answers
    )

# ── Step 2: Load index from ChromaDB ─────────────────────────────
def load_index():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context
    )
    return index

# ── Step 3: Score confidence based on retrieved nodes ────────────
def compute_confidence(source_nodes: list) -> float:
    """
    Confidence is based on the similarity scores of retrieved chunks.
    LlamaIndex returns scores between 0 and 1.
    We average the top results to get an overall confidence score.
    """
    if not source_nodes:
        return 0.0

    scores = [node.score for node in source_nodes if node.score is not None]

    if not scores:
        return 0.5  # Neutral confidence if no scores returned

    avg_score = sum(scores) / len(scores)
    return round(avg_score, 4)

# ── Step 4: Build the query engine ───────────────────────────────
def build_query_engine(index):
    return index.as_query_engine(
        similarity_top_k=3,           # Retrieve top 3 most relevant chunks
        text_qa_template=SUPPORT_PROMPT,
        response_mode="compact"       # Concise, merged response
    )

# ── Step 5: Main query function ───────────────────────────────────
def query(user_message: str) -> dict:
    """
    Main function called by the API.
    Returns a dict with: answer, confidence, escalate flag, sources
    """
    configure_settings()
    index = load_index()
    query_engine = build_query_engine(index)

    # Run the RAG query 
    response = query_engine.query(user_message)

    # Score confidence
    confidence = compute_confidence(response.source_nodes)

    # Decide whether to escalate to human
    # Escalate if: low confidence OR the LLM admitted it doesn't know
    no_answer_phrases = [
        "i don't have enough information to answer that",
        "let me connect you with a human agent who can help",
        "i cannot answer this question",
    ]
    answer_lower = str(response).lower()
    llm_admitted_ignorance = any(phrase in answer_lower for phrase in no_answer_phrases)

    escalate = (confidence < CONFIDENCE_THRESHOLD) or llm_admitted_ignorance

    # Extract source document names for transparency
    sources = list(set([
        os.path.basename(node.metadata.get("file_name", "unknown"))
        for node in response.source_nodes
    ]))

    return {
        "answer": str(response),
        "confidence": confidence,
        "escalate": escalate,
        "sources": sources
    }

# ── Quick test ────────────────────────────────────────────────────
if __name__ == "__main__":
    test_questions = [
        "What is your return policy?",
        "How do I track my order?",
        "Do you sell motorcycles?",        # Should trigger escalation
    ]

    print("\n[TEST] Running query engine tests...\n")
    print("=" * 60)

    for question in test_questions:
        print(f"\nQuestion : {question}")
        result = query(question)
        print(f"Answer   : {result['answer']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Escalate : {result['escalate']}")
        print(f"Sources  : {result['sources']}")
        print("-" * 60)