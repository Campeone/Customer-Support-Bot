import os
from dotenv import load_dotenv

import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings

load_dotenv()

# ── Configuration ────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "shopease_support"

# ── Step 1: Configure LlamaIndex global settings ─────────────────
def configure_settings():
    Settings.embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    Settings.text_splitter = SentenceSplitter(
        chunk_size=256,
        chunk_overlap=20
    )

# ── Step 2: Load documents ────────────────────────────────────────
def load_documents():
    print(f"[INFO] Loading documents from: {DATA_DIR}")
    documents = SimpleDirectoryReader(DATA_DIR).load_data()
    print(f"[OK] Loaded {len(documents)} document(s)")
    return documents

# ── Step 3: Set up ChromaDB ───────────────────────────────────────
def setup_chromadb():
    print(f"[INFO] Setting up ChromaDB at: {CHROMA_DIR}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    print(f"[OK] Collection '{COLLECTION_NAME}' ready")
    return chroma_collection

# ── Step 4: Build and persist the index ──────────────────────────
def build_index(documents, chroma_collection):
    print("[INFO] Building vector index (this may take a moment)...")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )

    print("[OK] Index built and persisted to ChromaDB!")
    return index

# ── Main ──────────────────────────────────────────────────────────
def ingest():
    print("\n[START] Starting ShopEase document ingestion...\n")

    configure_settings()
    documents = load_documents()
    chroma_collection = setup_chromadb()
    index = build_index(documents, chroma_collection)

    print("\n[DONE] Ingestion complete!")
    print("Stats:")
    print(f"   Documents loaded : {len(documents)}")
    print(f"   Collection name  : {COLLECTION_NAME}")
    print(f"   Vector store     : {CHROMA_DIR}")
    print("\nYou can now run the query engine.\n")

    return index

if __name__ == "__main__":
    ingest()