import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_name: str = os.getenv("APP_NAME", "ProContracts")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    db_path: str = os.getenv("DB_PATH", "procontracts.db")
    session_timeout_minutes: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "120"))
    offline_first: bool = os.getenv("OFFLINE_FIRST", "true").lower() == "true"
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "none")
    seed_admin_username: str = os.getenv("SEED_ADMIN_USERNAME", "admin")
    seed_admin_password: str = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    lmstudio_host: str = os.getenv("LMSTUDIO_HOST", "http://localhost:1234")
    lmstudio_model: str = os.getenv("LMSTUDIO_MODEL", "local-model")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def setup_logging() -> None:
    settings = get_settings()
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
