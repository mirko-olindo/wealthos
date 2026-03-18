from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime


# ── Vehicle ──────────────────────────────────────────────────────────────────

class VehicleCreate(BaseModel):
    name: str
    asset_class: Optional[str] = None
    manager: Optional[str] = None
    vehicle_type: Optional[str] = None
    currency: str = "EUR"
    vintage_year: Optional[int] = None
    commitment: Optional[float] = None
    notes: Optional[str] = None


class VehicleOut(VehicleCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int
    original_filename: str
    file_type: Optional[str]
    doc_category: Optional[str]
    vehicle_id: Optional[int]
    doc_date: Optional[date]
    extraction_status: str
    extraction_raw: Optional[Any]
    file_size: int
    uploaded_at: datetime
    extracted_at: Optional[datetime]

    class Config:
        from_attributes = True


# ── NAV Statement ─────────────────────────────────────────────────────────────

class NavStatementCreate(BaseModel):
    vehicle_id: int
    document_id: Optional[int] = None
    nav_date: date
    nav_value: float
    currency: str = "EUR"
    shares_units: Optional[float] = None
    nav_per_unit: Optional[float] = None
    notes: Optional[str] = None


class NavStatementOut(NavStatementCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Distribution ──────────────────────────────────────────────────────────────

class DistributionCreate(BaseModel):
    vehicle_id: int
    document_id: Optional[int] = None
    payment_date: date
    amount: float
    currency: str = "EUR"
    distribution_type: Optional[str] = None
    notes: Optional[str] = None


class DistributionOut(DistributionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Capital Call ──────────────────────────────────────────────────────────────

class CapitalCallCreate(BaseModel):
    vehicle_id: int
    document_id: Optional[int] = None
    call_date: date
    due_date: Optional[date] = None
    amount: float
    currency: str = "EUR"
    call_number: Optional[int] = None
    purpose: Optional[str] = None
    paid: int = 0
    notes: Optional[str] = None


class CapitalCallOut(CapitalCallCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Position ──────────────────────────────────────────────────────────────────

class PositionCreate(BaseModel):
    vehicle_id: int
    document_id: Optional[int] = None
    position_date: date
    invested_capital: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_gain: Optional[float] = None
    tvpi: Optional[float] = None
    dpi: Optional[float] = None
    irr: Optional[float] = None
    currency: str = "EUR"


class PositionOut(PositionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard aggregates ──────────────────────────────────────────────────────

class KpiSummary(BaseModel):
    total_nav: float
    total_invested: float
    total_distributions: float
    avg_tvpi: Optional[float]
    total_vehicles: int
    total_documents: int


class AllocationItem(BaseModel):
    asset_class: str
    nav_value: float
    percentage: float
    vehicle_count: int


class CashFlowItem(BaseModel):
    year: int
    inflows: float   # distribuzioni
    outflows: float  # capital calls
    net: float


class NavHistoryPoint(BaseModel):
    date: date
    nav: float
    vehicle_id: int
    vehicle_name: str


class VehicleSummary(BaseModel):
    id: int
    name: str
    asset_class: Optional[str]
    manager: Optional[str]
    currency: str
    latest_nav: Optional[float]
    invested_capital: Optional[float]
    tvpi: Optional[float]
    irr: Optional[float]
    last_updated: Optional[date]
