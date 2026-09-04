import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/reconciler")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    PORT: int = int(os.getenv("PORT", "8000"))
    ENV: str = os.getenv("ENV", "development")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
