from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_server_url: str = "http://localhost:8001"
    active_model_name: str = "densenet121"

    model_config = {"env_prefix": ""}


settings = Settings()
