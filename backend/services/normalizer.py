"""
Normalizzazione: prende il JSON estratto da Claude e popola il database.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.db import Document, Vehicle, NavStatement, Distribution, CapitalCall, Position


def parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m"]:
        try:
            return datetime.strptime(d[:10], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


async def find_or_suggest_vehicle(db: AsyncSession, vehicle_name: Optional[str], manager: Optional[str]) -> Optional[int]:
    """Cerca un veicolo esistente per nome (fuzzy) o restituisce None."""
    if not vehicle_name:
        return None
    result = await db.execute(select(Vehicle).where(Vehicle.name.ilike(f"%{vehicle_name}%")))
    vehicle = result.scalar_one_or_none()
    return vehicle.id if vehicle else None


async def apply_extraction(db: AsyncSession, document: Document, extraction: dict) -> dict:
    """
    Applica i dati estratti al database.
    Ritorna un riepilogo delle operazioni effettuate.
    """
    applied = []
    errors = []

    if "error" in extraction:
        return {"applied": [], "errors": [extraction["error"]]}

    # Aggiorna metadati documento
    if extraction.get("doc_date"):
        document.doc_date = parse_date(extraction["doc_date"])
    if extraction.get("doc_category"):
        document.doc_category = extraction["doc_category"]

    # Trova o associa veicolo
    vehicle_id = document.vehicle_id
    if not vehicle_id:
        vehicle_id = await find_or_suggest_vehicle(
            db,
            extraction.get("vehicle_name"),
            extraction.get("manager")
        )
        if vehicle_id:
            document.vehicle_id = vehicle_id

    if not vehicle_id:
        return {
            "applied": [],
            "errors": ["Nessun veicolo associato al documento. Associa manualmente il veicolo e ri-estrai."],
            "suggested_vehicle": extraction.get("vehicle_name")
        }

    # ── NAV Statement ─────────────────────────────────────────────────────────
    nav_data = extraction.get("nav", {})
    if nav_data and nav_data.get("value") and nav_data.get("date"):
        try:
            nav = NavStatement(
                vehicle_id=vehicle_id,
                document_id=document.id,
                nav_date=parse_date(nav_data["date"]),
                nav_value=float(nav_data["value"]),
                currency=extraction.get("currency", "EUR"),
                nav_per_unit=nav_data.get("per_unit"),
                shares_units=nav_data.get("units"),
            )
            db.add(nav)
            applied.append("nav_statement")
        except Exception as e:
            errors.append(f"NAV: {e}")

    # ── Distribution ──────────────────────────────────────────────────────────
    dist_data = extraction.get("distribution", {})
    if dist_data and dist_data.get("amount"):
        try:
            dist = Distribution(
                vehicle_id=vehicle_id,
                document_id=document.id,
                payment_date=parse_date(dist_data.get("payment_date")) or (document.doc_date or date.today()),
                amount=float(dist_data["amount"]),
                currency=extraction.get("currency", "EUR"),
                distribution_type=dist_data.get("type"),
            )
            db.add(dist)
            applied.append("distribution")
        except Exception as e:
            errors.append(f"Distribution: {e}")

    # ── Capital Call ──────────────────────────────────────────────────────────
    cc_data = extraction.get("capital_call", {})
    if cc_data and cc_data.get("amount"):
        try:
            cc = CapitalCall(
                vehicle_id=vehicle_id,
                document_id=document.id,
                call_date=parse_date(cc_data.get("call_date")) or (document.doc_date or date.today()),
                due_date=parse_date(cc_data.get("due_date")),
                amount=float(cc_data["amount"]),
                currency=extraction.get("currency", "EUR"),
                call_number=cc_data.get("call_number"),
                purpose=cc_data.get("purpose"),
            )
            db.add(cc)
            applied.append("capital_call")
        except Exception as e:
            errors.append(f"CapitalCall: {e}")

    # ── Position ──────────────────────────────────────────────────────────────
    pos_data = extraction.get("position", {})
    if pos_data and any(pos_data.get(k) for k in ["invested_capital", "current_value", "tvpi"]):
        try:
            pos = Position(
                vehicle_id=vehicle_id,
                document_id=document.id,
                position_date=document.doc_date or date.today(),
                invested_capital=pos_data.get("invested_capital"),
                current_value=pos_data.get("current_value"),
                tvpi=pos_data.get("tvpi"),
                dpi=pos_data.get("dpi"),
                irr=pos_data.get("irr"),
                currency=extraction.get("currency", "EUR"),
            )
            db.add(pos)
            applied.append("position")
        except Exception as e:
            errors.append(f"Position: {e}")

    document.extraction_status = "done"
    document.extracted_at = datetime.utcnow()
    await db.commit()

    return {"applied": applied, "errors": errors}
