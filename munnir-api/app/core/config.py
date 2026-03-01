from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./munnir.db"
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]
    SECRET_KEY: str = "dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # News ingestion
    NEWSAPI_KEY: str = ""
    NEWSAPI_BASE_URL: str = "https://newsapi.org/v2"
    NEWS_MAX_ARTICLES: int = 20
    NEWS_MAX_AGE_HOURS: int = 24

    # AI analysis (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_TIMEOUT_SECONDS: int = 60
    GEMINI_MAX_NEWS_TOKENS: int = 4000

    # Optional background scheduler
    NEWS_SCHEDULER_ENABLED: bool = False
    NEWS_SCHEDULER_INTERVAL_MINUTES: int = 30

    # Auto-pilot
    AUTOPILOT_ENABLED: bool = False
    AUTOPILOT_INTERVAL_MINUTES: int = 15

    # Trade execution
    PRICE_API_PROVIDER: str = "yfinance"
    TRADE_FEE_CENTS: int = 100  # $1.00 flat fee
    SLIPPAGE_ENABLED: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
