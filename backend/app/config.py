"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://timetracker_user:password@db:5432/timetracker"

    # JWT
    JWT_SECRET: str = "change-me-to-a-very-long-random-string-at-least-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Admin initial account
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123"

    # CORS
    CORS_ORIGINS: str = "http://localhost,http://localhost:80,http://127.0.0.1"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Time zone
    TZ: str = "Europe/Berlin"

    # Company defaults
    DEFAULT_VACATION_DAYS: int = 30

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
