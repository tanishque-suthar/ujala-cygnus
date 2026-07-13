from fastapi import APIRouter, Request

from app.schemas.models import HealthResponse
from app.services.model_client import ModelClient

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    client: ModelClient = request.app.state.model_client
    model_health = await client.health()
    reachable = model_health.get("status") == "ok"
    return HealthResponse(status="ok", model_server_reachable=reachable)
