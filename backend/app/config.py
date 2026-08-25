from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "group-subscription-manager"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/group_subs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
