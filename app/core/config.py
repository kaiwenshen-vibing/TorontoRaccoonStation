from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str | None = None
    cors_allowed_origins: str | None = None

    def get_cors_allowed_origins(self) -> list[str]:
        if self.cors_allowed_origins:
            return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]
        return [
            "http://localhost:8081",
            "http://127.0.0.1:8081",
            "http://localhost:19006",
            "http://127.0.0.1:19006",
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
