from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, screen
from app.services.model_client import ModelClient


@asynccontextmanager
async def lifespan(app: FastAPI):
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
