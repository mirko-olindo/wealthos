import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models.database import get_db
from backend.models.db import Document
from backend.models.schemas import DocumentOut
from backend.extractors.claude_extractor import extract_from_document
from backend.services.normalizer import apply_extraction

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png", "webp"}


def get_file_type(filename: str) -> str:
    return Path(filename).suffix.lstrip(".").lower()


async def process_document_background(doc_id: int, file_path: str, file_type: str, db_url: str):
    """Background task: estrae dati e normalizza nel DB."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine(db_url)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if not doc:
            return

        doc.extraction_status = "processing"
        await db.commit()

        try:
            extraction = await extract_from_document(file_path, file_type)
            doc.extraction_raw = extraction
            await apply_extraction(db, doc, extraction)
        except Exception as e:
            doc.extraction_status = "failed"
            doc.extraction_error = str(e)
            await db.commit()

    await engine.dispose()


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    vehicle_id: Optional[int] = Form(None),
    doc_category: Optional[str] = Form(None),
    auto_extract: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """Carica un documento nel repository. Avvia estrazione automatica se richiesto."""
    file_type = get_file_type(file.filename)
    if file_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Tipo file non supportato: {file_type}. Supportati: {', '.join(ALLOWED_EXTENSIONS)}")

    # Salva file con nome univoco
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = file_path.stat().st_size

    # Crea record nel DB
    doc = Document(
        filename=unique_name,
        original_filename=file.filename,
        file_path=str(file_path),
        file_type=file_type,
        doc_category=doc_category,
        vehicle_id=vehicle_id,
        extraction_status="pending" if auto_extract else "skipped",
        file_size=file_size,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Avvia estrazione in background
    if auto_extract and os.getenv("ANTHROPIC_API_KEY"):
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/wealthos.db")
        background_tasks.add_task(
            process_document_background, doc.id, str(file_path), file_type, db_url
        )

    return doc


@router.get("/", response_model=List[DocumentOut])
async def list_documents(
    vehicle_id: Optional[int] = None,
    doc_category: Optional[str] = None,
    extraction_status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Document).order_by(Document.uploaded_at.desc()).limit(limit)
    if vehicle_id:
        q = q.where(Document.vehicle_id == vehicle_id)
    if doc_category:
        q = q.where(Document.doc_category == doc_category)
    if extraction_status:
        q = q.where(Document.extraction_status == extraction_status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    return doc


@router.post("/{doc_id}/extract")
async def re_extract(doc_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Ri-avvia l'estrazione automatica per un documento già caricato."""
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Documento non trovato")

    doc.extraction_status = "pending"
    doc.extraction_error = None
    await db.commit()

    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/wealthos.db")
    background_tasks.add_task(
        process_document_background, doc.id, doc.file_path, doc.file_type, db_url
    )
    return {"message": "Estrazione avviata"}


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Documento non trovato")
    # Rimuovi file fisico
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    await db.delete(doc)
    await db.commit()
    return {"message": "Documento eliminato"}
