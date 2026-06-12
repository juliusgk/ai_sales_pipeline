"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://sales_user:changeme@localhost:5432/sales_pipeline"
    )

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3:8b"
    ollama_embed_model: str = "nomic-embed-text"
    embedding_dimension: int = 768

    # API Security
    api_key: str = "changeme-generate-a-strong-key"

    # Gmail Integration
    gmail_client_id: str = ""
    gmail_client_secret: str = ""

    # App
    secret_key: str = "changeme-generate-a-secret-key"
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sync_database_url(self) -> str:
        """Synchronous DB URL for Alembic migrations."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")


settings = Settings()
