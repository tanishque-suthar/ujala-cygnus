from pathlib import Path

from pydantic_settings import BaseSettings

# Project root = three levels up from this file (backend/app/config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_server_url: str = "http://localhost:8001"
    db_path: str = str(_PROJECT_ROOT / "database" / "cygnus.db")
    uploads_dir: str = str(_PROJECT_ROOT / "database" / "uploads")

    model_config = {"env_prefix": ""}

    @property
    def db_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def images_dir(self) -> Path:
        return Path(self.uploads_dir) / "images"

    @property
    def heatmaps_dir(self) -> Path:
        return Path(self.uploads_dir) / "heatmaps"


settings = Settings()
