# Deploy: Vercel (frontend + API) + Neon

## Architecture

```text
Browser → Vercel frontend (Next.js)
                ↓
         Vercel API project (FastAPI)
                ↓
              Neon Postgres
```

Two Vercel projects from the same GitHub repo (simplest, reliable).

---

## 1. Neon

1. Schema already applied (`database/schema.sql`) and data seeded.
2. Connection string form for the API:

```text
postgresql+asyncpg://USER:PASSWORD@HOST/neondb?sslmode=require
```

---

## 2. Vercel project A — API

1. [vercel.com/new](https://vercel.com/new) → import this GitHub repo.
2. Settings:

| Field | Value |
|--------|--------|
| **Root Directory** | `api` |
| **Framework** | Other / FastAPI (auto if detected) |
| **Install** | `pip install -r requirements.txt` (default) |

3. **Environment variables** (API project — required):

| Key | Value |
|-----|--------|
| `USE_SQLITE` | `false` |
| `DATABASE_URL` | `postgresql+asyncpg://USER:PASS@HOST/neondb?sslmode=require` |
| `SEED_ON_STARTUP` | `false` |
| `REPLACE_SEED_ON_STARTUP` | `false` |
| `TRUSTED_HOSTS` | `["*"]` |
| `ENVIRONMENT` | `development` |
| `CORS_ORIGINS` | `["https://your-frontend.vercel.app"]` |

If the function returns **500 FUNCTION_INVOCATION_FAILED**, open Vercel → Project → **Logs**.

Common cause: duplicate env vars. Example: `USE_SQLITE` set twice becomes `false\nfalse` and crashes Settings. In Vercel → **Settings → Environment Variables**, keep **one** row per key with a single value (`false` or `true`, no quotes, no line breaks). Then **Redeploy**.

4. Deploy. Note the URL, e.g. `https://ppca-api.vercel.app`.

5. Test:

- `https://ppca-api.vercel.app/health`
- `https://ppca-api.vercel.app/api/v1/scandals`

---

## 3. Vercel project B — frontend

1. **Add New Project** → same GitHub repo again.
2. Settings:

| Field | Value |
|--------|--------|
| **Root Directory** | `frontend` |
| **Framework** | Next.js |

3. **Environment variable:**

| Key | Value |
|-----|--------|
| `NEXT_PUBLIC_API_URL` | `https://ppca-api.vercel.app` (no trailing slash) |

4. Deploy. Note the URL, e.g. `https://ppca-web.vercel.app`.

---

## 4. Lock CORS

On the **API** project, set:

```text
CORS_ORIGINS=["https://ppca-web.vercel.app"]
```

Redeploy the API project. Add preview URLs to the JSON array if you use them.

---

## Local demo (unchanged)

```bash
# API
cd api && pip install -r requirements.txt
# scrapers (optional): pip install -r ../scrapers/requirements.txt
uvicorn app.main:app --reload --port 7860

# Frontend
cd frontend && pnpm install && pnpm dev
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API 500 / DB error | `USE_SQLITE=false` + valid `postgresql+asyncpg` Neon URL |
| Empty list | Neon has no rows; seed once locally against Neon |
| Browser CORS / `NetworkError when attempting to fetch resource` | Client pages proxy via Next rewrites (`/api` → `NEXT_PUBLIC_API_URL`). Redeploy **frontend** after setting that env. API also allows `*.vercel.app` via CORS regex; still set `CORS_ORIGINS` to your exact frontend URL. |
| Cold start slow | First request after idle can take a few seconds on Hobby |
