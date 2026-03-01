from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./munnir.db"
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
