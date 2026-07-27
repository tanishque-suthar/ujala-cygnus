import httpx

from app.config import settings

MODEL_SERVER_URL = settings.model_server_url
TIMEOUT = 30.0


class ModelServerError(Exception):
    pass


class ModelClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=MODEL_SERVER_URL,
            timeout=TIMEOUT,
        )

    async def predict(self, file_bytes: bytes, filename: str) -> dict:
        try:
            resp = await self._client.post(
                "/predict",
                files={"file": (filename, file_bytes)},
            )
        except httpx.TimeoutException:
            raise ModelServerError("Model server timed out")
        except httpx.RequestError:
            raise ModelServerError("Model server unreachable")

        if resp.status_code != 200:
            detail = f"Model server returned {resp.status_code}"
            try:
                body = resp.json()
                if "error" in body:
                    detail += f": {body['error']}"
            except Exception:
                pass
            raise ModelServerError(detail)

        return resp.json()

    async def health(self) -> dict:
        try:
            resp = await self._client.get("/health", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            return {"status": "unreachable", "model_loaded": False}

    async def close(self) -> None:
        await self._client.aclose()
