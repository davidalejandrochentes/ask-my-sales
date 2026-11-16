import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str | None
    nvidia_base_url: str
    nvidia_model: str | None
    db_path: str


def get_settings() -> Settings:
    return Settings(
        nvidia_api_key=os.getenv("NVIDIA_API_KEY"),
        nvidia_base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        nvidia_model=os.getenv("NVIDIA_MODEL"),
        db_path=os.getenv("DB_PATH", "data/orders.db"),
    )
