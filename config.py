import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# General configuration
DEBUG = True
MODEL = "llama-3.2-3b-instruct"
AI_NAME = "Camille"
USER_NAME = "Carlos"
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
OPENAI_API_BASE = "http://localhost:1234/v1"
OPENAI_KEY = "not-needed"

if not PICOVOICE_ACCESS_KEY:
    raise ValueError(
        "PICOVOICE_ACCESS_KEY env var is required to run this software. Please add it to .env")

# Tools configuration
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
OPENWEATHERMAP_DEFAULT_CITY = os.getenv("OPENWEATHERMAP_DEFAULT_CITY")
BRAVE_SEARCH_API_TOKEN = os.getenv("BRAVE_SEARCH_API_TOKEN")
