from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    content_dir: Path = Path(__file__).resolve().parent.parent.parent / "content"
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # DB — SQLite 로컬 개발 기본값. 배포 시 DATABASE_URL 환경변수로 PostgreSQL 등 교체.
    database_url: str = "sqlite:///./dev.db"

    # JWT — JWT_SECRET 은 배포 시 반드시 환경변수로 강한 랜덤값으로 교체.
    jwt_secret: str = "change-me-in-production-use-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_expires_days: int = 7

    # Google OAuth — frontend 가 받은 ID token 을 검증할 때 audience 비교
    google_client_id: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
