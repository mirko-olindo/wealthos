from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.schemas import KpiSummary, AllocationItem, CashFlowItem, VehicleSummary
from backend.services.aggregator import (
    get_kpi_summary,
    get_allocation,
    get_cashflow_by_year,
    get_nav_history,
    get_vehicles_summary,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpi", response_model=KpiSummary)
async def kpi(db: AsyncSession = Depends(get_db)):
    """KPI principali del portafoglio."""
    return await get_kpi_summary(db)


@router.get("/allocation", response_model=List[AllocationItem])
async def allocation(db: AsyncSession = Depends(get_db)):
    """Allocazione per asset class."""
    return await get_allocation(db)


@router.get("/cashflow", response_model=List[CashFlowItem])
async def cashflow(db: AsyncSession = Depends(get_db)):
    """Cash flow annuale (distribuzioni vs capital calls)."""
    return await get_cashflow_by_year(db)


@router.get("/nav-history")
async def nav_history(vehicle_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Storico NAV per tutti i veicoli o filtrato per veicolo."""
    return await get_nav_history(db, vehicle_id)


@router.get("/vehicles-summary", response_model=List[VehicleSummary])
async def vehicles_summary(db: AsyncSession = Depends(get_db)):
    """Riepilogo performance per ogni veicolo."""
    return await get_vehicles_summary(db)
