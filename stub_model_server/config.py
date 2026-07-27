from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_weights: str = "densenet121-res224-all"


settings = Settings()
