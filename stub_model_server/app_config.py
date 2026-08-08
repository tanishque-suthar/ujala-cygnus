from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_weights: str = "densenet121-res224-all"
    model_backend: str = "biomedclip"  # override with MODEL_BACKEND env var: "biomedclip" | "densenet"
    checkpoint_path: str = "biomedclip/best_checkpoint.pt"  # override with CHECKPOINT_PATH
    thresholds_path: str = "biomedclip/calibrated_thresholds.json"  # override with THRESHOLDS_PATH


settings = Settings()
