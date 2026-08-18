# ── Base image ────────────────────────────────────────────────────
FROM python:3.12-slim

# ── Set working directory ─────────────────────────────────────────
WORKDIR /app

# ── Install system dependencies ───────────────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Copy requirements and install Python deps ─────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy project files ────────────────────────────────────────────
COPY app.py .
COPY backend/ ./backend/
COPY data/ ./data/
COPY start.sh .

# ── Create runtime directories ────────────────────────────────────
RUN mkdir -p tickets chroma_db

# ── Make startup script executable ───────────────────────────────
RUN chmod +x start.sh

# ── Expose Streamlit port ─────────────────────────────────────────
EXPOSE 7860

# ── Streamlit configuration ───────────────────────────────────────
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ── Start via shell script ────────────────────────────────────────
CMD ["./start.sh"]