from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Configuration settings for the application.
    Loaded from .env file or environment variables.
    """

    # Define allowed origins for CORS
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
    ]

    # --- THIS IS THE FIX ---
    # We are temporarily COMMENTING OUT the Config class.
    # This stops pydantic-settings from actively trying to
    # load a .env file that might be misconfigured.
    # It will now ONLY use the default values above.
    # We will re-enable this in when we add GEMINI_API_KEY.

    # class Config:
    #     env_file = ".env"
    #     env_file_encoding = "utf-8"
    # ---------------------


# Create a single, importable instance of the settings
settings = Settings()
