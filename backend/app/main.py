import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents, health, patients, screen
from app.services.model_client import ModelClient


def _run_migrations() -> None:
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    settings.heatmaps_dir.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(_run_migrations)
    app.state.model_client = ModelClient()
    yield
    await app.state.model_client.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screen.router)
app.include_router(health.router)
app.include_router(patients.router)
app.include_router(documents.router)
