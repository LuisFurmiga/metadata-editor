from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Metadados"
    max_upload_size: int = 250 * 1024 * 1024
    workspace_root: Path = Path.home() / ".metadata-editor" / "sessions"
    session_ttl_seconds: int = 24 * 60 * 60
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    exiftool_binary: str = "exiftool"
    model_config = SettingsConfigDict(env_prefix="METADATA_", env_file=".env")


settings = Settings()
