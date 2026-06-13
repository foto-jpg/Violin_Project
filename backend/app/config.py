import os
from pathlib import Path
from pydantic_settings import BaseSettings

_default_data = Path("/app/data") if Path("/app/data").exists() else Path(__file__).resolve().parents[2] / "data"


class Settings(BaseSettings):
    data_dir: Path = _default_data
    audiveris_image: str = "violin-checker-audiveris:latest"
    max_upload_mb: int = 50
    job_timeout_sec: int = 600

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
