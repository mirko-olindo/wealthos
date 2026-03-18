import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from backend.models.database import init_db
from backend.routers import documents, vehicles, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inizializza DB e cartelle
    Path("./data").mkdir(exist_ok=True)
    Path("./uploads").mkdir(exist_ok=True)
    await init_db()
    yield
    # Shutdown: niente da fare per ora


app = FastAPI(
    title="WealthOS API",
    description="Piattaforma per la gestione e visualizzazione di portafogli di investimento",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers API
app.include_router(documents.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")

# Serve frontend statico
frontend_dist = Path("./frontend/dist")
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = frontend_dist / "index.html"
        return FileResponse(str(index))
else:
    @app.get("/")
    async def root():
        return {
            "message": "WealthOS API attiva",
            "docs": "/docs",
            "version": "1.0.0"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
