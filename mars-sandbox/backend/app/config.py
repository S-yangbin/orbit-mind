"""Configuration loader from .env file."""
from pathlib import Path
from dotenv import load_dotenv
import os

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "mars-sandbox")
    APP_ENV: str = os.getenv("APP_ENV", "production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "please-set-in-env-or-dotenv")

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "mars_sandbox")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )

    # Auth
    AUTH_USERNAME: str = os.getenv("AUTH_USERNAME", "admin")
    AUTH_PASSWORD: str = os.getenv("AUTH_PASSWORD", "")

    # File paths
    HTML_ROOT: str = os.getenv("HTML_ROOT", "/mnt/oss-sybuddy/html")
    THUMBNAIL_DIR: str = os.getenv("THUMBNAIL_DIR", "/mnt/oss-sybuddy/data/thumbnails")

    # Scan
    SCAN_INTERVAL: int = int(os.getenv("SCAN_INTERVAL", "300"))

    # Node management
    NODE_API_KEY: str = os.getenv("NODE_API_KEY", "change-me-node-api-key")
    NODE_STALE_SECONDS: int = int(os.getenv("NODE_STALE_SECONDS", "180"))

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
