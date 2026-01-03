"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database (Neon PostgreSQL)
    DATABASE_URL: str

    # Redis (Upstash)
    REDIS_URL: str

    # Solana
    SOLANA_RPC_URL: str
    SOLANA_PROGRAM_ID: str = "E6tuNWDutZ7Npsb6UU6GmV5H4B3ucpAwzzGeqJzrUUJz"
    PROGRAM_ID: str = "E6tuNWDutZ7Npsb6UU6GmV5H4B3ucpAwzzGeqJzrUUJz"  # Alias for compatibility
    ADMIN_WALLET_PUBKEY: str = "BNa6ccCgyxkuVmjRpv1h64Hd6nWnnNNKZvmXKbwY1u4m"
    ADMIN_PRIVATE_KEY: str = ""  # Base58 encoded private key for admin operations
    TREASURY_WALLET_PUBKEY: str = "CR6Uxh1R3bkvfgB2qma5C7x4JNkWH1mxBERoEmmGrfrm"
    POINTS_MINT_ADDRESS: str = ""  # POINTS SPL token mint address

    # Anthropic
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5-20250929"

    # Tournament
    MAX_TOURNAMENT_BUDGET_MULTIPLIER: float = 3.0
    DECISION_TIMEOUT_NORMAL: int = 5
    DECISION_TIMEOUT_ALLIN: int = 10

    # Security
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # Encryption
    PROMPT_ENCRYPTION_KEY: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
