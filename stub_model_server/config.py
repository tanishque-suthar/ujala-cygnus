from pathlib import Path

from pydantic_settings import BaseSettings

_PACKAGE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_weights_path: str = str(_PACKAGE_DIR / "best_biomedclip_model.pth")

    model_config = {"env_prefix": ""}


settings = Settings()
