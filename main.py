import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.models.database import init_db
from backend.routers import documents, vehicles, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("./data").mkdir(parents=True, exist_ok=True)
    Path("./uploads").mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="WealthOS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

frontend_html = Path("./frontend/index.html")

@app.get("/")
async def root():
    if frontend_html.exists():
        return FileResponse(str(frontend_html))
    return JSONResponse({"message": "WealthOS API attiva", "docs": "/docs"})

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    if frontend_html.exists():
        return FileResponse(str(frontend_html))
    return JSONResponse({"message": "WealthOS API attiva"})
