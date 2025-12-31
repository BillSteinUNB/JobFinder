"""Configuration management using pydantic-settings."""

import os
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Adzuna API
    adzuna_app_id: str = Field(default="", description="Adzuna API App ID")
    adzuna_app_key: str = Field(default="", description="Adzuna API Key")

    # Database paths
    metadata_db_path: Path = Field(
        default=PROJECT_ROOT / "data" / "jobs.db",
        description="Path to SQLite metadata database",
    )
    chroma_persist_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "chromadb",
        description="ChromaDB persistence directory",
    )
    chroma_collection: str = Field(
        default="jobs",
        description="ChromaDB collection name",
    )

    # Embeddings
    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )

    # App
    app_env: str = Field(default="local", description="Environment (local/prod)")

    @property
    def is_adzuna_configured(self) -> bool:
        """Check if Adzuna API credentials are configured."""
        return bool(self.adzuna_app_id and self.adzuna_app_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
