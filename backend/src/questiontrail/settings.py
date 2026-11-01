from pathlib import Path
from typing import Any, Literal
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_files() -> tuple[Path, ...]:
    """Locate .env file in project root or current working directory.
    
    Structure:
      .../QuestionTrail/backend/src/questiontrail/settings.py
      parents[0] = questiontrail
      parents[1] = src
      parents[2] = backend
      parents[3] = QuestionTrail (project root)
    """
    settings_file = Path(__file__).resolve()
    project_root = settings_file.parents[3]
    root_env = project_root / ".env"
    cwd_env = Path.cwd() / ".env"

    files: list[Path] = []
    if root_env.is_file():
        files.append(root_env)
    if cwd_env.is_file() and cwd_env not in files:
        files.append(cwd_env)
    if not files:
        # Fallback to root_env even if not yet created so pydantic can load it
        files.append(root_env)
    return tuple(files)


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    model_config = SettingsConfigDict(
        env_file=_resolve_env_files(),
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
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Google Gemini Model name"
    )

    @field_validator("nvidia_api_key", "gemini_api_key", mode="before")
    @classmethod
    def clean_empty_keys(cls, v: Any) -> Any:
        """Treat empty or whitespace-only keys as None."""
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @property
    def has_nvidia_configured(self) -> bool:
        """Check if NVIDIA API key is configured with a non-empty value."""
        return bool(self.nvidia_api_key and self.nvidia_api_key.get_secret_value().strip())

    @property
    def has_gemini_configured(self) -> bool:
        """Check if Gemini API key is configured with a non-empty value."""
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())


# Cached or dependency-injectable settings instance
def get_settings() -> Settings:
    return Settings()


def print_provider_status(settings: Settings | None = None) -> None:
    """Print selected provider mode and configuration status with strict credential privacy."""
    s = settings or get_settings()
    print(f"Selected provider mode: {s.llm_provider}")
    print(f"NVIDIA configured: {s.has_nvidia_configured}")
    print(f"Gemini configured: {s.has_gemini_configured}")

