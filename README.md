---
title: Pakistan Public Corruption Atlas API
emoji: 🌙
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Public OSINT research API for documented corruption cases (1960–2026)
---

# Pakistan Public Corruption Atlas

OSINT research and visualization platform covering publicly documented corruption-related proceedings involving Pakistani public officials, institutions, procurement, and state-owned entities (**1960–2026**).

> **Disclaimer:** This project aggregates publicly available information from reputable and official sources for research, transparency, and educational purposes. **Inclusion in the database does not imply guilt.** Users should consult the cited primary sources and court records for authoritative information.

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Framer Motion, ECharts, Leaflet, React Flow |
| Backend | FastAPI, SQLAlchemy (async), Pydantic |
| Database | PostgreSQL (Neon-ready) with SQLite demo fallback |
| Search | PostgreSQL FTS + optional Meilisearch |
| Scrapers | BeautifulSoup, Scrapy-ready modular pipeline, Newspaper3k, Pandas |
| Deploy | Docker (API / Hugging Face Spaces style), Vercel (frontend) |

## Repository layout

```
api/                 FastAPI application
frontend/            Next.js dashboard
scrapers/            OSINT pipeline (fetch → parse → clean → verify → stage)
database/schema.sql  Canonical PostgreSQL schema
data/sample/         Seed dataset with citations
docs/                Architecture & ethics docs
docker-compose.yml   Postgres + Meilisearch + API
```

## Quick start (local demo)

### 1. API

```bash
cd api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 7860
```

API docs: http://localhost:7860/docs

### 2. Frontend

```bash
cd frontend
pnpm install
copy .env.local.example .env.local
pnpm dev
```

Dashboard: http://localhost:3000

### 3. Docker (Postgres + API)

```bash
docker compose up --build
```

API on http://localhost:7860 (set `USE_SQLITE=false` via compose).

## Legal status labels

Every record distinguishes procedural stages — never treated as interchangeable:

Alleged · Under Investigation · Charged · On Trial · Convicted · Acquitted · Case Dismissed · Pending · Official Inquiry · Investigative Journalism Report

## Verification rules

- Minimum **two independent** reputable sources
- Prefer official documents (court, AGP, NAB, Gazette, PPRA)
- Citation for claims; confidence score High / Medium / Low
- Allowlisted domains only; robots.txt + rate limits in scrapers
- No social media rumors, blogs, anonymous forums

## Scraping pipeline

```bash
# from repo root
python scrapers/pipeline.py --seeds --out data/staging/candidates.jsonl
python scrapers/pipeline.py --url https://www.agp.gov.pk/ --rpm 4
```

Modules: `scrapers/` (fetch/rate-limit/robots), `parser/`, `cleaner/`, `verifier/`, `database/` (JSONL staging).

## Export

- JSON: `GET /api/v1/export/json`
- CSV: `GET /api/v1/export/csv`

## Tests

```bash
cd api
pytest -q
```

## Deployment notes

- **Frontend (Vercel):** set `NEXT_PUBLIC_API_URL` to your API origin. Security headers are set in `frontend/next.config.ts`.
- **Backend (Docker / Hugging Face Spaces):** use `api/Dockerfile` (port **7860**). Point `DATABASE_URL` at Neon Postgres for production; keep `SEED_ON_STARTUP` only for demos. Set `ENVIRONMENT=production` (forces seed off, docs off, requires non-SQLite).
- **Security:** see [docs/SECURITY.md](docs/SECURITY.md) for rate limits, CORS, API keys, and the production checklist.
- **Meilisearch:** optional; enable `USE_MEILISEARCH=true` after indexing.

## Ethics

See [docs/ETHICS.md](docs/ETHICS.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/SECURITY.md](docs/SECURITY.md).

Avoid political branding. This is a journalism / transparency research tool.
