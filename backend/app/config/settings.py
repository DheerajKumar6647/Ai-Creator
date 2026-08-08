import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "InterviewAI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Database Settings
    DATABASE_URL: str = "sqlite:////tmp/interview_ai.db" if os.environ.get("VERCEL") else "sqlite:///./interview_ai.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

