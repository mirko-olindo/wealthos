"""
Aggregazioni per la dashboard: KPI, allocazione, cash flow, storico NAV.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date
from typing import Optional, List

from backend.models.db import Vehicle, NavStatement, Distribution, CapitalCall, Position, Document
from backend.models.schemas import KpiSummary, AllocationItem, CashFlowItem, VehicleSummary


async def get_kpi_summary(db: AsyncSession) -> KpiSummary:
    """KPI principali: NAV totale, capitale investito, distribuzioni, TVPI medio."""

    # NAV totale: somma degli ultimi NAV per ogni veicolo
    subq = (
        select(NavStatement.vehicle_id, func.max(NavStatement.nav_date).label("max_date"))
        .group_by(NavStatement.vehicle_id)
        .subquery()
    )
    latest_navs = await db.execute(
        select(func.sum(NavStatement.nav_value))
        .join(subq, and_(
            NavStatement.vehicle_id == subq.c.vehicle_id,
            NavStatement.nav_date == subq.c.max_date
        ))
    )
    total_nav = latest_navs.scalar() or 0.0

    # Capitale investito: somma delle capital calls pagate
    invested_result = await db.execute(select(func.sum(CapitalCall.amount)))
    total_invested = invested_result.scalar() or 0.0

    # Distribuzioni totali
    dist_result = await db.execute(select(func.sum(Distribution.amount)))
    total_distributions = dist_result.scalar() or 0.0

    # TVPI medio (dalle posizioni più recenti)
    tvpi_result = await db.execute(select(func.avg(Position.tvpi)).where(Position.tvpi.isnot(None)))
    avg_tvpi = tvpi_result.scalar()

    # Conteggi
    v_count = await db.execute(select(func.count(Vehicle.id)))
    d_count = await db.execute(select(func.count(Document.id)))

    return KpiSummary(
        total_nav=round(total_nav, 2),
        total_invested=round(total_invested, 2),
        total_distributions=round(total_distributions, 2),
        avg_tvpi=round(avg_tvpi, 2) if avg_tvpi else None,
        total_vehicles=v_count.scalar() or 0,
        total_documents=d_count.scalar() or 0,
    )


async def get_allocation(db: AsyncSession) -> List[AllocationItem]:
    """Allocazione per asset class basata sugli ultimi NAV."""
    subq = (
        select(NavStatement.vehicle_id, func.max(NavStatement.nav_date).label("max_date"))
        .group_by(NavStatement.vehicle_id)
        .subquery()
    )
    rows = await db.execute(
        select(Vehicle.asset_class, func.sum(NavStatement.nav_value).label("nav"), func.count(Vehicle.id).label("cnt"))
        .join(subq, and_(
            NavStatement.vehicle_id == subq.c.vehicle_id,
            NavStatement.nav_date == subq.c.max_date
        ))
        .join(Vehicle, Vehicle.id == NavStatement.vehicle_id)
        .group_by(Vehicle.asset_class)
    )
    items = rows.all()
    total = sum(r.nav for r in items) or 1
    return [
        AllocationItem(
            asset_class=r.asset_class or "Non classificato",
            nav_value=round(r.nav, 2),
            percentage=round(r.nav / total * 100, 1),
            vehicle_count=r.cnt,
        )
        for r in sorted(items, key=lambda x: x.nav, reverse=True)
    ]


async def get_cashflow_by_year(db: AsyncSession) -> List[CashFlowItem]:
    """Cash flow annuale: distribuzioni (inflows) vs capital calls (outflows)."""
    dist_rows = await db.execute(
        select(func.strftime("%Y", Distribution.payment_date).label("year"), func.sum(Distribution.amount).label("total"))
        .group_by(func.strftime("%Y", Distribution.payment_date))
    )
    cc_rows = await db.execute(
        select(func.strftime("%Y", CapitalCall.call_date).label("year"), func.sum(CapitalCall.amount).label("total"))
        .group_by(func.strftime("%Y", CapitalCall.call_date))
    )

    inflows = {r.year: r.total for r in dist_rows.all()}
    outflows = {r.year: r.total for r in cc_rows.all()}
    years = sorted(set(list(inflows.keys()) + list(outflows.keys())))

    return [
        CashFlowItem(
            year=int(y),
            inflows=round(inflows.get(y, 0), 2),
            outflows=round(outflows.get(y, 0), 2),
            net=round(inflows.get(y, 0) - outflows.get(y, 0), 2),
        )
        for y in years
    ]


async def get_nav_history(db: AsyncSession, vehicle_id: Optional[int] = None):
    """Storico NAV per tutti i veicoli o per un veicolo specifico."""
    q = select(NavStatement, Vehicle.name.label("vehicle_name")).join(Vehicle, Vehicle.id == NavStatement.vehicle_id)
    if vehicle_id:
        q = q.where(NavStatement.vehicle_id == vehicle_id)
    q = q.order_by(NavStatement.nav_date)
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "date": str(r.NavStatement.nav_date),
            "nav": r.NavStatement.nav_value,
            "vehicle_id": r.NavStatement.vehicle_id,
            "vehicle_name": r.vehicle_name,
        }
        for r in rows
    ]


async def get_vehicles_summary(db: AsyncSession) -> List[VehicleSummary]:
    """Riepilogo per ogni veicolo con ultimo NAV e metriche di performance."""
    vehicles_result = await db.execute(select(Vehicle))
    vehicles = vehicles_result.scalars().all()

    summaries = []
    for v in vehicles:
        # Ultimo NAV
        nav_result = await db.execute(
            select(NavStatement).where(NavStatement.vehicle_id == v.id).order_by(NavStatement.nav_date.desc()).limit(1)
        )
        latest_nav = nav_result.scalar_one_or_none()

        # Ultima posizione
        pos_result = await db.execute(
            select(Position).where(Position.vehicle_id == v.id).order_by(Position.position_date.desc()).limit(1)
        )
        latest_pos = pos_result.scalar_one_or_none()

        summaries.append(VehicleSummary(
            id=v.id,
            name=v.name,
            asset_class=v.asset_class,
            manager=v.manager,
            currency=v.currency,
            latest_nav=round(latest_nav.nav_value, 2) if latest_nav else None,
            invested_capital=round(latest_pos.invested_capital, 2) if latest_pos and latest_pos.invested_capital else None,
            tvpi=round(latest_pos.tvpi, 2) if latest_pos and latest_pos.tvpi else None,
            irr=round(latest_pos.irr, 2) if latest_pos and latest_pos.irr else None,
            last_updated=latest_nav.nav_date if latest_nav else None,
        ))
    return summaries
