"""Configuration loader from .env file."""
from pathlib import Path
from dotenv import load_dotenv
import os
import shutil

_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def _find_exe(name: str, fallback: str = "") -> str:
    """Find executable in PATH, with fallback."""
    found = shutil.which(name)
    if found:
        return found
    # Common alternative paths
    extras = [
        "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin",
        "/snap/bin", "/home/linuxbrew/.linuxbrew/bin",
    ]
    for base in extras:
        candidate = os.path.join(base, name)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return fallback or name

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "mars-sandbox")
    APP_ENV: str = os.getenv("APP_ENV", "production")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "please-set-in-env-or-dotenv")

    # Database
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql")  # mysql or sqlite
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "mars_sandbox")

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_TYPE == "sqlite":
            return "sqlite:///./mars_sandbox_test.db"
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
    VIDEO_ROOT: str = os.getenv("VIDEO_ROOT", "/mnt/oss-sybuddy/videos")
    VIDEO_AUDIO_DIR: str = os.getenv("VIDEO_AUDIO_DIR", "/mnt/oss-sybuddy/video-audio")
    VIDEO_NOTES_DIR: str = os.getenv("VIDEO_NOTES_DIR", "/mnt/oss-sybuddy/video-notes")
    MEAL_PHOTO_DIR: str = os.getenv("MEAL_PHOTO_DIR", "/mnt/oss-sybuddy/data/meals")
    WALLPAPER_DIR: str = os.getenv("WALLPAPER_DIR", "/mnt/oss-sybuddy/data/wallpapers")

    # Scan
    SCAN_INTERVAL: int = int(os.getenv("SCAN_INTERVAL", "300"))

    # Node management
    NODE_API_KEY: str = os.getenv("NODE_API_KEY", "change-me-node-api-key")
    NODE_STALE_SECONDS: int = int(os.getenv("NODE_STALE_SECONDS", "180"))

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Bailian CLI
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # OSS (for signed video URLs)
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "please-set-endpoint")
    OSS_BUCKET: str = os.getenv("OSS_BUCKET", "sybuddy")
    OSS_ACCESS_KEY_ID: str = os.getenv("OSS_ACCESS_KEY_ID", "")
    OSS_ACCESS_KEY_SECRET: str = os.getenv("OSS_ACCESS_KEY_SECRET", "")
    OSS_ROLE_ARN: str = os.getenv("OSS_ROLE_ARN", "")

    @property
    def oss_video_base_url(self) -> str:
        return f"https://{self.OSS_BUCKET}.{self.OSS_ENDPOINT}/videos"

    # Weather (OpenWeatherMap)
    OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")
    WEATHER_LAT: str = os.getenv("WEATHER_LAT", "30.29")  # 杭州余杭区
    WEATHER_LON: str = os.getenv("WEATHER_LON", "120.30")
    WEATHER_CITY: str = os.getenv("WEATHER_CITY", "杭州")

    # Wallpaper (Pexels — 随机壁纸补充源)
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

    # External tool paths (auto-detected, can override via env)
    @property
    def FFMPEG_PATH(self) -> str:
        return os.getenv("FFMPEG_PATH") or _find_exe("ffmpeg")

    @property
    def BL_PATH(self) -> str:
        return os.getenv("BL_PATH") or _find_exe("bl")

settings = Settings()
