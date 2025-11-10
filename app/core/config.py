from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    Loaded from .env file or environment variables.
    """

    # Define allowed origins for CORS
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]

    GEMINI_API_KEY: Optional[str] = None
    PLANNER_GEMINI_MODEL: str = "gemini-2.0-flash"
    WRITER_GEMINI_MODEL: str = "gemini-2.0-flash"


# Create a single, importable instance of the settings
settings = Settings()
