# Architecture

Pakistan Public Corruption Atlas — research & education only. Coverage window **1960–2026**.

## Data flow

```
Allowlisted OSINT sources
        │
        ▼
  scrapers (robots + rate limit + cache + retry)
        │
        ▼
  parser → cleaner → verifier (≥2 sources, confidence)
        │
        ▼
  staging JSONL / PostgreSQL upsert
        │
        ▼
  FastAPI (query, analytics, export)
        │
        ▼
  Next.js dashboard (charts, map, network, citations)
```

## API surface

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/scandals` | Filtered, paginated case list |
| `GET /api/v1/scandals/{id}` | Case detail + citations + timeline |
| `GET /api/v1/stats/dashboard` | Home metrics |
| `GET /api/v1/stats/map` | Geolocated points |
| `GET /api/v1/analytics/trends` | Trends & durations |
| `GET /api/v1/analytics/sankey` | Documented amount flows |
| `GET /api/v1/network/graph` | People / institution / case graph |
| `GET /api/v1/search` | Keyword search |
| `GET /api/v1/export/json\|csv` | Full export with sources |

## Schema highlights

- `scandals` — core record with legal status enum and confidence
- `sources` — per-claim citations (`quote_or_claim`, `is_primary`)
- `timeline_events` — dated procedural milestones
- `individuals` / `institutions` — normalized entities
- `scrape_runs` / `source_cache` — pipeline observability

See `database/schema.sql` for the full PostgreSQL definition. SQLAlchemy models in `api/app/models` mirror the schema for SQLite demos and Postgres.

## Frontend routes

- `/` dashboard
- `/cases` filters + list
- `/cases/[id]` detail + citations
- `/timeline` year zoom
- `/map` Leaflet heatmap-style clusters
- `/analytics` charts, Sankey, React Flow network
- `/search` individual / institution / keyword

## Production checklist

1. Neon Postgres + run `database/schema.sql` then optional `database/roles.sql`
2. Deploy API on Vercel (`api/` root) with Neon `DATABASE_URL`; seed off
3. Deploy frontend on Vercel (`frontend/` root); set `NEXT_PUBLIC_API_URL`
4. Set API `CORS_ORIGINS` to the frontend Vercel URL
5. See [DEPLOY.md](DEPLOY.md) and [SECURITY.md](SECURITY.md)
