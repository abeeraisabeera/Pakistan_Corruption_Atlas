"""Dashboard and analytics aggregations."""
from __future__ import annotations

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Individual, LegalStatus, Scandal, ScandalIndividual
from app.schemas.scandal import DashboardStats
from app.services.labels import DISCLAIMER
from app.services.scandals import _source_counts, to_list_item

_PUBLISHED = and_(Scandal.is_published.is_(True), Scandal.deleted_at.is_(None))


async def dashboard_stats(session: AsyncSession) -> DashboardStats:
    total = await session.scalar(select(func.count()).select_from(Scandal).where(_PUBLISHED)) or 0
    total_pkr = (
        await session.scalar(select(func.coalesce(func.sum(Scandal.amount_pkr), 0)).where(_PUBLISHED)) or 0
    )
    total_usd = (
        await session.scalar(select(func.coalesce(func.sum(Scandal.amount_usd), 0)).where(_PUBLISHED)) or 0
    )

    by_year_rows = (
        await session.execute(
            select(func.extract("year", Scandal.start_date).label("year"), func.count())
            .where(_PUBLISHED)
            .group_by("year")
            .order_by("year")
        )
    ).all()
    by_year = [{"year": int(y), "count": c} for y, c in by_year_rows if y is not None]

    by_province_rows = (
        await session.execute(
            select(Scandal.province, func.count())
            .where(_PUBLISHED, Scandal.province.is_not(None))
            .group_by(Scandal.province)
            .order_by(func.count().desc())
        )
    ).all()
    by_province = [{"province": p, "count": c} for p, c in by_province_rows]

    by_inst_rows = (
        await session.execute(
            select(Scandal.institution, func.count())
            .where(_PUBLISHED, Scandal.institution.is_not(None))
            .group_by(Scandal.institution)
            .order_by(func.count().desc())
            .limit(15)
        )
    ).all()
    by_institution = [{"institution": i, "count": c} for i, c in by_inst_rows]

    by_cat_rows = (
        await session.execute(
            select(Scandal.category, func.count()).where(_PUBLISHED).group_by(Scandal.category)
        )
    ).all()
    by_category = [{"category": cat.value if hasattr(cat, "value") else cat, "count": c} for cat, c in by_cat_rows]

    by_status_rows = (
        await session.execute(
            select(Scandal.current_legal_status, func.count())
            .where(_PUBLISHED)
            .group_by(Scandal.current_legal_status)
        )
    ).all()
    by_status = [
        {"status": st.value if hasattr(st, "value") else st, "count": c} for st, c in by_status_rows
    ]

    by_sector_rows = (
        await session.execute(
            select(Scandal.sector, func.count())
            .where(_PUBLISHED, Scandal.sector.is_not(None))
            .group_by(Scandal.sector)
            .order_by(func.count().desc())
        )
    ).all()
    by_sector = [{"sector": s, "count": c} for s, c in by_sector_rows]

    by_case_type_rows = (
        await session.execute(
            select(Scandal.case_type, func.count())
            .where(_PUBLISHED, Scandal.case_type.is_not(None))
            .group_by(Scandal.case_type)
            .order_by(func.count().desc())
        )
    ).all()
    by_case_type = [{"case_type": ct, "count": c} for ct, c in by_case_type_rows]

    by_party_rows = (
        await session.execute(
            select(Individual.political_party, func.count(func.distinct(ScandalIndividual.scandal_id)))
            .join(ScandalIndividual, ScandalIndividual.individual_id == Individual.id)
            .join(Scandal, Scandal.id == ScandalIndividual.scandal_id)
            .where(_PUBLISHED, Individual.political_party.is_not(None))
            .group_by(Individual.political_party)
            .order_by(func.count(func.distinct(ScandalIndividual.scandal_id)).desc())
        )
    ).all()
    by_party = [{"party": p, "count": c} for p, c in by_party_rows]

    convictions = await session.scalar(
        select(func.count()).where(_PUBLISHED, Scandal.current_legal_status == LegalStatus.CONVICTION)
    ) or 0
    acquittals = await session.scalar(
        select(func.count()).where(_PUBLISHED, Scandal.current_legal_status == LegalStatus.ACQUITTAL)
    ) or 0
    dismissed = await session.scalar(
        select(func.count()).where(_PUBLISHED, Scandal.current_legal_status == LegalStatus.CASE_DISMISSED)
    ) or 0
    resolved = convictions + acquittals + dismissed
    conviction_stats = {
        "convictions": convictions,
        "acquittals": acquittals,
        "dismissed": dismissed,
        "resolved": resolved,
        "conviction_rate": round(convictions / resolved, 4) if resolved else None,
        "note": (
            "Rates reflect documented procedural outcomes in this dataset only — "
            "not a national judicial conviction rate."
        ),
    }

    latest_rows = (
        await session.execute(
            select(Scandal).where(_PUBLISHED).order_by(Scandal.updated_at.desc()).limit(8)
        )
    ).scalars().all()
    counts = await _source_counts(session, [r.id for r in latest_rows])
    latest = [to_list_item(r, counts.get(r.id, 0)) for r in latest_rows]

    return DashboardStats(
        total_scandals=total,
        total_estimated_pkr=float(total_pkr),
        total_estimated_usd=float(total_usd),
        by_year=by_year,
        by_province=by_province,
        by_institution=by_institution,
        by_category=by_category,
        by_status=by_status,
        by_sector=by_sector,
        by_case_type=by_case_type,
        by_party=by_party,
        conviction_stats=conviction_stats,
        latest=latest,
        disclaimer=DISCLAIMER,
    )


async def money_by_year(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(
                func.extract("year", Scandal.start_date).label("year"),
                func.coalesce(func.sum(Scandal.amount_pkr), 0),
                func.count(),
            )
            .where(_PUBLISHED)
            .group_by("year")
            .order_by("year")
        )
    ).all()
    return [
        {"year": int(y), "amount_pkr": float(a), "count": c}
        for y, a, c in rows
        if y is not None
    ]


async def investigation_duration(session: AsyncSession) -> list[dict]:
    """Days between start and end where both dates exist (documented span only)."""
    rows = (
        await session.execute(
            select(
                Scandal.public_id,
                Scandal.title,
                Scandal.start_date,
                Scandal.end_date,
                Scandal.current_legal_status,
            ).where(_PUBLISHED, Scandal.end_date.is_not(None))
        )
    ).all()
    out = []
    for public_id, title, start, end, status in rows:
        days = (end - start).days
        out.append(
            {
                "public_id": public_id,
                "title": title,
                "days": days,
                "status": status.value if hasattr(status, "value") else status,
            }
        )
    return sorted(out, key=lambda x: x["days"], reverse=True)


async def map_points(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(
                Scandal.public_id,
                Scandal.title,
                Scandal.province,
                Scandal.city,
                Scandal.latitude,
                Scandal.longitude,
                Scandal.category,
                Scandal.current_legal_status,
                Scandal.amount_pkr,
            ).where(
                _PUBLISHED,
                Scandal.latitude.is_not(None),
                Scandal.longitude.is_not(None),
            )
        )
    ).all()
    return [
        {
            "public_id": pid,
            "title": title,
            "province": province,
            "city": city,
            "lat": lat,
            "lng": lng,
            "category": cat.value if hasattr(cat, "value") else cat,
            "status": st.value if hasattr(st, "value") else st,
            "amount_pkr": float(amt) if amt is not None else None,
        }
        for pid, title, province, city, lat, lng, cat, st, amt in rows
    ]


async def build_network(session: AsyncSession) -> dict:
    scandals = (await session.execute(select(Scandal).where(_PUBLISHED))).scalars().all()
    published_ids = {s.id for s in scandals}
    individuals = (
        await session.execute(
            select(ScandalIndividual, Individual)
            .join(Individual, Individual.id == ScandalIndividual.individual_id)
            .where(ScandalIndividual.scandal_id.in_(published_ids) if published_ids else False)
        )
    ).all()

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for s in scandals:
        nodes[f"scandal:{s.id}"] = {
            "id": f"scandal:{s.id}",
            "label": s.public_id,
            "type": "scandal",
            "title": s.title,
            "group": "scandal",
        }
        if s.institution:
            iid = f"institution:{s.institution}"
            nodes[iid] = {
                "id": iid,
                "label": s.institution,
                "type": "institution",
                "group": "institution",
            }
            edges.append(
                {
                    "id": f"{s.id}-{iid}",
                    "source": f"scandal:{s.id}",
                    "target": iid,
                    "type": "involves_institution",
                }
            )

    for link, ind in individuals:
        nid = f"individual:{ind.id}"
        nodes[nid] = {
            "id": nid,
            "label": ind.full_name,
            "type": "individual",
            "party": ind.political_party,
            "group": "individual",
        }
        edges.append(
            {
                "id": f"{link.scandal_id}-{ind.id}",
                "source": f"scandal:{link.scandal_id}",
                "target": nid,
                "type": "involves_person",
                "position": link.position_held,
            }
        )

    return {"nodes": list(nodes.values()), "edges": edges}


async def sankey_money_flow(session: AsyncSession) -> dict:
    """Sankey: province -> category -> status using documented amounts only."""
    rows = (
        await session.execute(
            select(
                Scandal.province,
                Scandal.category,
                Scandal.current_legal_status,
                func.coalesce(func.sum(Scandal.amount_pkr), 0),
            )
            .where(
                _PUBLISHED,
                Scandal.amount_pkr.is_not(None),
                Scandal.province.is_not(None),
            )
            .group_by(Scandal.province, Scandal.category, Scandal.current_legal_status)
        )
    ).all()

    nodes_set: list[str] = []
    links: list[dict] = []

    def idx(name: str) -> int:
        if name not in nodes_set:
            nodes_set.append(name)
        return nodes_set.index(name)

    pc: dict[tuple[str, str], float] = {}
    cs: dict[tuple[str, str], float] = {}
    for province, category, status, amount in rows:
        cat = category.value if hasattr(category, "value") else str(category)
        st = status.value if hasattr(status, "value") else str(status)
        amt = float(amount)
        pc[(province, cat)] = pc.get((province, cat), 0) + amt
        cs[(cat, st)] = cs.get((cat, st), 0) + amt

    for (province, cat), amt in pc.items():
        links.append({"source": idx(f"Province: {province}"), "target": idx(f"Category: {cat}"), "value": amt})
    for (cat, st), amt in cs.items():
        links.append({"source": idx(f"Category: {cat}"), "target": idx(f"Status: {st}"), "value": amt})

    return {"nodes": [{"name": n} for n in nodes_set], "links": links}
