import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.model_client import ModelClient


@pytest.fixture(autouse=True)
def _setup_app_state():
    app.state.model_client = ModelClient()


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
