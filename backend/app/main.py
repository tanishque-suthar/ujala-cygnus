import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents, health, patients, screen, reports
from app.services.ocr_service import OCRService
from app.services.model_client import ModelClient


def _run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    settings.heatmaps_dir.mkdir(parents=True, exist_ok=True)
    (settings.reports_dir / "temp").mkdir(parents=True, exist_ok=True)
    
    app.state.ocr_service = OCRService()
    if not OCRService.check_availability():
        import logging
        logging.getLogger("uvicorn").warning("Tesseract not found — OCR endpoints will fail")
        
    await asyncio.to_thread(_run_migrations)
    client = ModelClient()
    app.state.model_client = client
    health_data = await client.health()
    app.state.active_model_name = health_data.get("model_backend", "unknown")
    yield
    await app.state.model_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screen.router)
app.include_router(health.router)
app.include_router(patients.router)
app.include_router(documents.router)
app.include_router(reports.router)
