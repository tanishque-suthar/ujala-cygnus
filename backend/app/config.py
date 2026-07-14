from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_server_url: str = "http://localhost:8001"
    active_model_name: str = "biomedclip"

    model_config = {"env_prefix": ""}


settings = Settings()
