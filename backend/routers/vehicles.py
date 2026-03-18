from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.database import get_db
from backend.models.db import Vehicle, NavStatement, Distribution, CapitalCall, Position
from backend.models.schemas import VehicleCreate, VehicleOut, NavStatementCreate, NavStatementOut, \
    DistributionCreate, DistributionOut, CapitalCallCreate, CapitalCallOut, PositionCreate, PositionOut

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/", response_model=VehicleOut)
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db)):
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


@router.get("/", response_model=List[VehicleOut])
async def list_vehicles(
    asset_class: Optional[str] = None,
    manager: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Vehicle).order_by(Vehicle.name)
    if asset_class:
        q = q.where(Vehicle.asset_class == asset_class)
    if manager:
        q = q.where(Vehicle.manager.ilike(f"%{manager}%"))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Veicolo non trovato")
    return v


@router.put("/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(vehicle_id: int, data: VehicleCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Veicolo non trovato")
    for k, val in data.model_dump().items():
        setattr(v, k, val)
    await db.commit()
    await db.refresh(v)
    return v


@router.delete("/{vehicle_id}")
async def delete_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(404, "Veicolo non trovato")
    await db.delete(v)
    await db.commit()
    return {"message": "Veicolo eliminato"}


# ── NAV Statements ────────────────────────────────────────────────────────────

@router.post("/{vehicle_id}/nav", response_model=NavStatementOut)
async def add_nav(vehicle_id: int, data: NavStatementCreate, db: AsyncSession = Depends(get_db)):
    data.vehicle_id = vehicle_id
    nav = NavStatement(**data.model_dump())
    db.add(nav)
    await db.commit()
    await db.refresh(nav)
    return nav


@router.get("/{vehicle_id}/nav", response_model=List[NavStatementOut])
async def list_nav(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NavStatement).where(NavStatement.vehicle_id == vehicle_id).order_by(NavStatement.nav_date)
    )
    return result.scalars().all()


# ── Distributions ─────────────────────────────────────────────────────────────

@router.post("/{vehicle_id}/distributions", response_model=DistributionOut)
async def add_distribution(vehicle_id: int, data: DistributionCreate, db: AsyncSession = Depends(get_db)):
    data.vehicle_id = vehicle_id
    dist = Distribution(**data.model_dump())
    db.add(dist)
    await db.commit()
    await db.refresh(dist)
    return dist


@router.get("/{vehicle_id}/distributions", response_model=List[DistributionOut])
async def list_distributions(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Distribution).where(Distribution.vehicle_id == vehicle_id).order_by(Distribution.payment_date)
    )
    return result.scalars().all()


# ── Capital Calls ─────────────────────────────────────────────────────────────

@router.post("/{vehicle_id}/capital-calls", response_model=CapitalCallOut)
async def add_capital_call(vehicle_id: int, data: CapitalCallCreate, db: AsyncSession = Depends(get_db)):
    data.vehicle_id = vehicle_id
    cc = CapitalCall(**data.model_dump())
    db.add(cc)
    await db.commit()
    await db.refresh(cc)
    return cc


@router.get("/{vehicle_id}/capital-calls", response_model=List[CapitalCallOut])
async def list_capital_calls(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CapitalCall).where(CapitalCall.vehicle_id == vehicle_id).order_by(CapitalCall.call_date)
    )
    return result.scalars().all()


# ── Positions ─────────────────────────────────────────────────────────────────

@router.post("/{vehicle_id}/positions", response_model=PositionOut)
async def add_position(vehicle_id: int, data: PositionCreate, db: AsyncSession = Depends(get_db)):
    data.vehicle_id = vehicle_id
    pos = Position(**data.model_dump())
    db.add(pos)
    await db.commit()
    await db.refresh(pos)
    return pos


@router.get("/{vehicle_id}/positions", response_model=List[PositionOut])
async def list_positions(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Position).where(Position.vehicle_id == vehicle_id).order_by(Position.position_date)
    )
    return result.scalars().all()
