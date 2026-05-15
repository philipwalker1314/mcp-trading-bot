from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =====================================================
    # APP
    # =====================================================

    APP_NAME: str = "MCP Trading Bot"

    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: Literal[
        "development",
        "staging",
        "production",
    ] = "development"

    DEBUG: bool = True

    # NEW:
    # Prevent TradingBot from auto-starting
    # while testing infrastructure/migrations
    ENABLE_TRADING: bool = False

    API_HOST: str = "0.0.0.0"

    API_PORT: int = 8000

    # =====================================================
    # DATABASE
    # =====================================================

    POSTGRES_HOST: str = "db"

    POSTGRES_PORT: int = 5432

    POSTGRES_USER: str = "user"

    POSTGRES_PASSWORD: str = "password"

    POSTGRES_DB: str = "trading"

    DATABASE_URL: str | None = None

    # =====================================================
    # REDIS
    # =====================================================

    REDIS_HOST: str = "redis"

    REDIS_PORT: int = 6379

    REDIS_URL: str | None = None

    # =====================================================
    # BINANCE
    # =====================================================

    BINANCE_API_KEY: str = "CHANGE_ME"

    BINANCE_SECRET_KEY: str = "CHANGE_ME"

    BINANCE_TESTNET: bool = True

    PAPER_TRADING: bool = True

    # =====================================================
    # NVIDIA / DEEPSEEK
    # =====================================================

    DEEPSEEK_API_KEY: str = "CHANGE_ME"

    DEEPSEEK_BASE_URL: str = (
        "https://api.deepseek.com"
    )

    DEEPSEEK_MODEL: str = (
        "deepseek-v4-flash"
    )

    # =====================================================
    # RISK
    # =====================================================

    MAX_RISK_PER_TRADE: float = 0.01

    MAX_DAILY_DRAWDOWN: float = 0.05

    MAX_OPEN_POSITIONS: int = 3

    # =====================================================
    # LOGGING
    # =====================================================

    LOG_LEVEL: str = "INFO"

    # =====================================================
    # VALIDATORS
    # =====================================================

    @field_validator("MAX_RISK_PER_TRADE")
    @classmethod
    def validate_risk(
        cls,
        value: float,
    ):

        if value <= 0 or value > 0.05:

            raise ValueError(
                "Invalid MAX_RISK_PER_TRADE"
            )

        return value

    # =====================================================
    # CONNECTION HELPERS
    # =====================================================

    @property
    def postgres_url(self):

        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            "postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def redis_connection_url(self):

        if self.REDIS_URL:
            return self.REDIS_URL

        return (
            f"redis://"
            f"{self.REDIS_HOST}:"
            f"{self.REDIS_PORT}"
        )


@lru_cache
def get_settings():

    return Settings()


settings = get_settings()
