import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG: bool = True
    MODEL_NAME: str = os.getenv("MODEL_NAME", "")
    AI_NAME: str = "Camille"
    USER_NAME: str = "Carlos"
    PICOVOICE_ACCESS_KEY: str = os.getenv("PICOVOICE_ACCESS_KEY", "")
    OPENAI_API_BASE: str = "http://localhost:1234/v1"
    OPENAI_KEY: str = "not-needed"
    
    # Tools configuration
    OPENWEATHERMAP_API_KEY: Optional[str] = os.getenv("OPENWEATHERMAP_API_KEY")
    OPENWEATHERMAP_DEFAULT_CITY: Optional[str] = os.getenv("OPENWEATHERMAP_DEFAULT_CITY")
    BRAVE_SEARCH_API_TOKEN: Optional[str] = os.getenv("BRAVE_SEARCH_API_TOKEN")
    
    @classmethod
    def validate(cls) -> None:
        if not cls.MODEL_NAME:
            raise ValueError("MODEL_NAME env var is required")
        if not cls.PICOVOICE_ACCESS_KEY:
            raise ValueError("PICOVOICE_ACCESS_KEY env var is required")

# Validate on import
Config.validate()