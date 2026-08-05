<div align="center">

# 🌙 Pakistan Public Corruption Atlas

### OSINT research atlas · **1960–2026**

[![Live](https://img.shields.io/badge/🌐_Live_Demo-01411C?style=for-the-badge)](https://pakistan-corruption-atlas.vercel.app)
[![Cases](https://img.shields.io/badge/📂_Cases-0D7377?style=for-the-badge)](https://pakistan-corruption-atlas.vercel.app/cases)
[![License](https://img.shields.io/badge/License-MIT-D4AF37?style=for-the-badge)](LICENSE)

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=nextdotjs)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi&logoColor=white)](api/)
[![Postgres](https://img.shields.io/badge/Neon-Postgres-336791?style=flat-square&logo=postgresql&logoColor=white)](database/)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=flat-square&logo=vercel)](docs/DEPLOY.md)

Publicly sourced records of corruption-related proceedings involving Pakistani officials, institutions, procurement, and state entities — built for **research, transparency, and education**.

</div>

---

> **⚠️ Disclaimer**  
> Aggregates publicly available information from reputable and official sources.  
> **Inclusion does not imply guilt.** Always consult cited primary sources and court records.

---

## ✨ What you get

| | |
|:---|:---|
| 🗺️ **Case atlas** | Filterable records with status, province, category, and citations |
| ⏱️ **Timeline** | Chronological view of documented proceedings |
| 📊 **Analytics** | Trends, amounts, and relationship views |
| 📤 **Export** | JSON & CSV for researchers |
| 🔍 **Search** | Full-text search across titles, summaries, and institutions |

---

## 🏗️ Stack

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│    Neon     │
│  (Vercel)   │     │  (Vercel)   │     │  Postgres   │
└─────────────┘     └─────────────┘     └─────────────┘
```

| Layer | Tech |
|:------|:-----|
| **Frontend** | Next.js · React · TypeScript · Tailwind · Framer Motion · ECharts |
| **API** | FastAPI · SQLAlchemy (async) · Pydantic |
| **Data** | Neon Postgres · SQLite for local demos |
| **Ingest** | Modular scrapers (fetch → parse → clean → verify) |

---

## 🚀 Quick start

<details open>
<summary><b>① API</b> · port <code>7860</code></summary>

```bash
cd api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 7860
```

📖 Docs → [http://localhost:7860/docs](http://localhost:7860/docs)

</details>

<details open>
<summary><b>② Frontend</b> · port <code>3000</code></summary>

```bash
cd frontend
pnpm install
cp .env.local.example .env.local   # Windows: copy .env.local.example .env.local
pnpm dev
```

🖥️ App → [http://localhost:3000](http://localhost:3000)

</details>

<details>
<summary><b>③ Docker</b> · Postgres + API</summary>

```bash
docker compose up --build
```

</details>

---

## 📁 Layout

```text
PPCA/
├── api/            FastAPI app (Vercel root: api)
├── frontend/       Next.js dashboard (Vercel root: frontend)
├── scrapers/       OSINT ingest pipeline
├── database/       schema.sql · roles
├── data/sample/    Seed dataset + citations
└── docs/           Deploy · security · ethics · architecture
```

---

## 🏷️ Status labels

Procedural stages are **never** treated as interchangeable:

| Status | Meaning |
|:-------|:--------|
| Alleged | Public allegation / press report |
| Under Investigation | Agency examining the matter |
| Charged | Formal charges reported |
| On Trial | Court proceedings underway |
| Convicted / Acquitted | Court outcome |
| Official Inquiry | Inquiry / commission findings |
| Investigative Journalism | Originating journalism (not a verdict) |

Also: Case Dismissed · Pending · Civil Settlement · Closed · and more.

---

## ✅ Verification rules

- **Two independent** reputable sources minimum  
- Prefer official docs (court, AGP, NAB, Gazette, PPRA)  
- Confidence: **High** / **Medium** / **Low**  
- Allowlisted domains · robots.txt · rate limits  
- No rumors, blogs, or anonymous forums  

---

## 🔌 API snippets

```http
GET /health
GET /api/v1/scandals
GET /api/v1/scandals/{public_id}
GET /api/v1/export/json
GET /api/v1/export/csv
```

```bash
# Scrapers (from repo root)
python scrapers/pipeline.py --seeds --out data/staging/candidates.jsonl
python scrapers/pipeline.py --url https://www.agp.gov.pk/ --rpm 4

# Tests
cd api && pytest -q
```

---

## ☁️ Deploy

Full walkthrough → **[docs/DEPLOY.md](docs/DEPLOY.md)**

| Project | Root | Key env |
|:--------|:-----|:--------|
| **API** | `api` | `DATABASE_URL` · `USE_SQLITE=false` · `CORS_ORIGINS` |
| **Frontend** | `frontend` | `NEXT_PUBLIC_API_URL` → API origin (no trailing slash) |
| **DB** | Neon | Apply [`database/schema.sql`](database/schema.sql) |

Security checklist → [docs/SECURITY.md](docs/SECURITY.md)

---

## 📚 Docs

| Doc | |
|:----|:--|
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Ethics](docs/ETHICS.md) | Research & sourcing principles |
| [Security](docs/SECURITY.md) | Hardening for public-read OSS |
| [Deploy](docs/DEPLOY.md) | Vercel + Neon step-by-step |

---

<div align="center">

**Not affiliated with any political party or government body.**

Research & education only · Cite primary sources

<br/>

[🌐 Open the atlas](https://pakistan-corruption-atlas.vercel.app) · [📂 Browse cases](https://pakistan-corruption-atlas.vercel.app/cases)

</div>
