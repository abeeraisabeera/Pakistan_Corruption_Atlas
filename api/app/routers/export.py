"""CSV / JSON export of scandals with full citation fields."""
import csv
import io
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.deps import require_api_key
from app.middleware.rate_limit import client_ip
from app.models.entities import Scandal, ScandalIndividual, ScandalInstitution
from app.security.events import log_security_event
from app.security.turnstile import verify_turnstile
from app.services.labels import DISCLAIMER, status_label

router = APIRouter()

_BLOCKED_UA_FRAGMENTS = ("sqlmap", "nikto", "curl/", "wget/", "python-requests/", "scrapy")


def _row(scandal: Scandal) -> dict:
    people = [
        {
            "name": link.individual.full_name,
            "position": link.position_held,
            "party": link.individual.political_party,
        }
        for link in scandal.individuals
    ]
    sources = [
        {
            "title": s.title,
            "url": s.url,
            "publisher": s.publisher,
            "source_type": s.source_type,
            "published_date": s.published_date.isoformat() if s.published_date else None,
            "quote_or_claim": s.quote_or_claim,
            "is_primary": s.is_primary,
        }
        for s in scandal.sources
    ]
    return {
        "public_id": scandal.public_id,
        "title": scandal.title,
        "summary": scandal.summary,
        "start_date": scandal.start_date.isoformat(),
        "end_date": scandal.end_date.isoformat() if scandal.end_date else None,
        "province": scandal.province,
        "city": scandal.city,
        "institution": scandal.institution,
        "government_department": scandal.government_department,
        "category": scandal.category.value,
        "sector": scandal.sector,
        "amount_pkr": float(scandal.amount_pkr) if scandal.amount_pkr is not None else None,
        "amount_usd": float(scandal.amount_usd) if scandal.amount_usd is not None else None,
        "amount_notes": scandal.amount_notes,
        "current_legal_status": scandal.current_legal_status.value,
        "status_label": status_label(scandal.current_legal_status),
        "court_name": scandal.court_name,
        "case_number": scandal.case_number,
        "confidence_score": scandal.confidence_score.value,
        "individuals": people,
        "sources": sources,
        "source_urls": [s["url"] for s in sources],
        "disclaimer": DISCLAIMER,
    }


async def _guard_export(
    request: Request,
    cf_turnstile_response: str | None,
    x_api_key: str | None,
) -> None:
    if settings.require_api_key_for_export:
        await require_api_key(request, x_api_key)

    ua = (request.headers.get("user-agent") or "").lower()
    if not ua or any(frag in ua for frag in _BLOCKED_UA_FRAGMENTS):
        # Soft block obvious scrapers on export only; browsers still work.
        if settings.is_production or (ua and any(frag in ua for frag in ("sqlmap", "nikto"))):
            log_security_event(
                "export_blocked_ua",
                client_ip=client_ip(request),
                path=request.url.path,
                status=403,
                request_id=getattr(request.state, "request_id", None),
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Export blocked")

    if settings.turnstile_enforce_on_export:
        ok = await verify_turnstile(cf_turnstile_response, client_ip(request))
        if not ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CAPTCHA required")


async def _load_all(db: AsyncSession) -> list[Scandal]:
    result = await db.execute(
        select(Scandal)
        .where(Scandal.is_published.is_(True), Scandal.deleted_at.is_(None))
        .options(
            selectinload(Scandal.sources),
            selectinload(Scandal.individuals).selectinload(ScandalIndividual.individual),
            selectinload(Scandal.institutions_rel).selectinload(ScandalInstitution.institution),
        )
        .order_by(Scandal.start_date)
        .limit(settings.export_max_rows)
    )
    return list(result.scalars().unique().all())


@router.get("/json")
async def export_json(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cf_turnstile_response: str | None = Header(default=None, alias="CF-Turnstile-Response"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    await _guard_export(request, cf_turnstile_response, x_api_key)
    rows = [_row(s) for s in await _load_all(db)]
    payload = {
        "disclaimer": DISCLAIMER,
        "count": len(rows),
        "truncated": len(rows) >= settings.export_max_rows,
        "scandals": rows,
    }
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=ppca-export.json"},
    )


@router.get("/csv")
async def export_csv(
    request: Request,
    db: AsyncSession = Depends(get_db),
    cf_turnstile_response: str | None = Header(default=None, alias="CF-Turnstile-Response"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    await _guard_export(request, cf_turnstile_response, x_api_key)
    scandals = await _load_all(db)
    buffer = io.StringIO()
    fieldnames = [
        "public_id",
        "title",
        "start_date",
        "end_date",
        "province",
        "city",
        "institution",
        "category",
        "sector",
        "amount_pkr",
        "amount_usd",
        "amount_notes",
        "current_legal_status",
        "status_label",
        "confidence_score",
        "court_name",
        "case_number",
        "individuals",
        "source_urls",
        "disclaimer",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for s in scandals:
        row = _row(s)
        writer.writerow(
            {
                **{k: row.get(k) for k in fieldnames if k not in ("individuals", "source_urls")},
                "individuals": "; ".join(
                    f"{p['name']} ({p.get('position') or 'n/a'})" for p in row["individuals"]
                ),
                "source_urls": " | ".join(row["source_urls"]),
                "disclaimer": DISCLAIMER,
            }
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ppca-export.csv"},
    )
