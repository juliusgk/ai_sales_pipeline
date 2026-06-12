# AI Sales Pipeline

AI-powered sales pipeline assistant with a RAG-connected SLM for natural language queries about your leads, contacts, and deals.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI
- **Database**: PostgreSQL 16 + pgvector
- **SLM**: Ollama + Llama 3 8B (runs on CPU, no GPU required)
- **RAG**: LlamaIndex + nomic-embed-text embeddings
- **Dashboard**: Streamlit
- **Deployment**: Docker Compose + Caddy (auto-HTTPS)
- **Security**: API key auth, encrypted disk, HTTPS, non-root containers

## Quick Start (Cloud VM)

Recommended VM: **4 vCPU / 16 GB RAM / 50 GB SSD** (AWS t3.xlarge ~$50-80/mo)

```bash
# 1. SSH into your VM and clone
git clone https://github.com/juliusgk/ai_sales_pipeline.git
cd ai_sales_pipeline

# 2. Run the deployment script (installs Docker, generates secrets, starts everything)
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. Set up firewall
./scripts/setup_firewall.sh

# 4. Edit Caddyfile with your domain, then restart Caddy
nano Caddyfile
docker compose restart caddy
```

The deploy script will:
- Install Docker if not present
- Generate random API key, secret key, and DB password
- Build and start all 5 services
- Pull Llama 3 and nomic-embed-text models (~5 GB download)
- Run database migrations

## Architecture

```
Gmail API --------\
                   \
LinkedIn CSV -------> FastAPI Backend --> PostgreSQL + pgvector
                   /        |                    |
Manual entry -----/         |              LlamaIndex RAG
                            |                    |
                      Streamlit Dashboard   Ollama (Llama 3)
                            |                    |
                            +-------- Chat ------+
```

## API Endpoints

All endpoints require `Authorization: Bearer <API_KEY>` header.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/docs` | Swagger UI (no auth) |
| GET/POST | `/api/companies/` | List / create companies |
| GET/PATCH/DELETE | `/api/companies/{id}` | Get / update / delete company |
| GET/POST | `/api/contacts/` | List / create contacts |
| GET/POST | `/api/leads/` | List / create leads (filterable by status, source) |
| GET/POST | `/api/interactions/` | List / create interactions |
| GET/POST | `/api/deals/` | List / create deals |
| GET/POST | `/api/tags/` | List / create tags |
| POST | `/api/chat/` | Ask natural language questions (RAG) |
| GET | `/api/integrations/gmail/authorize` | Start Gmail OAuth2 flow |
| POST | `/api/integrations/gmail/sync` | Sync emails from Gmail |
| POST | `/api/integrations/linkedin/import/connections` | Import LinkedIn CSV |
| POST | `/api/integrations/linkedin/import/messages` | Import LinkedIn messages CSV |

## Dashboard Pages

1. **Pipeline Overview** - Kanban board with leads by status, filters, metrics
2. **Lead Detail** - Full lead info, edit forms, interaction timeline
3. **Interactions** - Filterable log of all touchpoints
4. **Analytics** - Funnel, conversion rates, activity charts (Plotly)
5. **Chat Assistant** - Natural language queries about your pipeline
6. **Settings** - Gmail/LinkedIn integration, tag management, data export

## Local Development (no Docker needed)

```bash
# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pip install aiosqlite  # for SQLite testing

# Run API with SQLite (no PostgreSQL or Ollama needed)
DATABASE_URL="sqlite+aiosqlite:///./dev.db" uvicorn src.main:app --reload

# API docs at http://localhost:8000/docs
# Default API key: changeme-generate-a-strong-key

# Run tests
pytest
```

Note: The AI chat feature requires Ollama running with models pulled. Everything else works without it.

## Security

- API key authentication on all endpoints (timing-safe comparison)
- Non-root Docker containers
- PostgreSQL bound to localhost only
- Caddy auto-HTTPS with Let's Encrypt
- UFW firewall: only ports 22, 80, 443
- Secrets generated at deploy time, stored in `.env` (never committed)
- Gmail OAuth tokens stored on encrypted disk
