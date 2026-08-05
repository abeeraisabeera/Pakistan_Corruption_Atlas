from functools import lru_cache
import os
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Pakistan Public Corruption Atlas"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://ppca:ppca@localhost:5432/ppca"
    use_sqlite: bool = True
    sqlite_url: str = "sqlite+aiosqlite:///./ppca.db"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    cors_allow_credentials: bool = False
    trusted_hosts: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "test",
            "testserver",
            "*.hf.space",
            "*.huggingface.co",
            "*.vercel.app",
        ]
    )

    meilisearch_url: str = "http://localhost:7700"
    meilisearch_key: str = "masterKey"
    use_meilisearch: bool = False

    seed_on_startup: bool = True
    replace_seed_on_startup: bool = True
    sample_data_path: str = "../ppca-export.json"

    disable_docs: bool | None = None
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_default: int = 120
    rate_limit_search: int = 60
    rate_limit_export: int = 10
    max_query_length: int = 200
    max_page_size: int = 100
    max_query_string_length: int = 2048
    export_max_rows: int = 5000

    api_key_hashes: list[str] = Field(default_factory=list)
    api_key_pepper: str = ""
    api_key_max_failures: int = 10
    api_key_lockout_seconds: int = 900
    require_api_key_for_export: bool = False

    turnstile_secret_key: str = ""
    turnstile_enforce_on_export: bool = False

    idempotency_ttl_seconds: int = 86400
    sentry_dsn: str = ""
    api_version: str = "1.0.0"

    @field_validator("cors_origins", "trusted_hosts", "api_key_hashes", mode="before")
    @classmethod
    def parse_json_list(cls, value):  # noqa: ANN001
        if value is None or value == "":
            return []
        if isinstance(value, str):
            import json

            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [part.strip() for part in text.split(",") if part.strip()]
        return value

    @field_validator(
        "use_sqlite",
        "seed_on_startup",
        "replace_seed_on_startup",
        "cors_allow_credentials",
        "use_meilisearch",
        "rate_limit_enabled",
        "require_api_key_for_export",
        "turnstile_enforce_on_export",
        mode="before",
    )
    @classmethod
    def parse_boolish(cls, value):  # noqa: ANN001
        """Vercel sometimes duplicates env values as 'false\\nfalse' — take the first line."""
        if isinstance(value, str):
            value = value.strip().splitlines()[0].strip().strip('"').strip("'")
            lowered = value.lower()
            if lowered in {"1", "true", "yes", "on"}:
                return True
            if lowered in {"0", "false", "no", "off"}:
                return False
        return value

    @model_validator(mode="after")
    def enforce_environment_guards(self) -> "Settings":
        # Vercel serverless: read-only FS except /tmp; never seed; allow all hosts
        if os.getenv("VERCEL"):
            self.seed_on_startup = False
            self.replace_seed_on_startup = False
            self.trusted_hosts = ["*"]
            if self.use_sqlite:
                self.sqlite_url = "sqlite+aiosqlite:////tmp/ppca.db"

        if self.environment == "production":
            self.seed_on_startup = False
            self.replace_seed_on_startup = False
            if self.use_sqlite and not os.getenv("VERCEL"):
                raise ValueError("USE_SQLITE must be false when ENVIRONMENT=production")
            if self.disable_docs is None:
                self.disable_docs = True
        elif self.disable_docs is None:
            self.disable_docs = False
        return self

    @property
    def docs_enabled(self) -> bool:
        return not bool(self.disable_docs)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
