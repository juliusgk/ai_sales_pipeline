# AI Sales Pipeline

AI-powered sales pipeline assistant with a RAG-connected SLM for natural language queries about your leads, contacts, and deals.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL 16 + pgvector
- **SLM**: Ollama + Llama 3 8B
- **RAG**: LlamaIndex + nomic-embed-text embeddings
- **Dashboard**: Streamlit
- **Deployment**: Docker Compose + Caddy (auto-HTTPS)

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your values

# 2. Start all services
docker compose up -d

# 3. Pull the LLM and embedding models
docker compose exec ollama ollama pull llama3:8b
docker compose exec ollama ollama pull nomic-embed-text

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Access the dashboard
# https://your-domain.com (or http://localhost:8501 for local dev)
```

## Architecture

```
Gmail/LinkedIn --> Integration Layer --> PostgreSQL + pgvector
                                              |
                                        LlamaIndex RAG
                                              |
                                     Ollama (Llama 3 8B)
                                              |
                                     FastAPI REST API
                                              |
                                    Streamlit Dashboard
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run API locally (requires PostgreSQL + Ollama running)
uvicorn src.main:app --reload

# Run tests
pytest
```
