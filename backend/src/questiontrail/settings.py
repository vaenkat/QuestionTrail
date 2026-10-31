from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Service configuration
    service_name: str = "QuestionTrail API"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    # Provider configuration
    llm_provider: Literal["auto", "nvidia", "gemini", "mock"] = Field(
        default="auto",
        description="Active LLM provider routing mode"
    )
    llm_fallback_order: list[str] = Field(
        default=["nvidia", "gemini", "cache"],
        description="Fallback order for structured generation"
    )

    # Provider credentials (server-side only, never exposed in responses)
    nvidia_api_key: SecretStr | None = Field(
        default=None,
        description="NVIDIA NIM API Key"
    )
    nvidia_model: str = Field(
        default="meta/llama-3.3-70b-instruct",
        description="NVIDIA NIM Model name"
    )
    gemini_api_key: SecretStr | None = Field(
        default=None,
        description="Optional Google Gemini API Key"
    )


# Cached or dependency-injectable settings instance
def get_settings() -> Settings:
    return Settings()
