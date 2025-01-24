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
MEMCACHED_HOST = os.getenv("MEMCACHED_HOST")
MEMCACHED_KEY = os.getenv("MEMCACHED_KEY")
OPENAI_API_BASE = "http://localhost:1234/v1"
OPENAI_KEY = "not-needed"

if not PICOVOICE_ACCESS_KEY:
    raise ValueError(
        "PICOVOICE_ACCESS_KEY env var is required to run this software. Please add it to .env")
if not MEMCACHED_HOST or not MEMCACHED_KEY:
    raise ValueError(
        "MEMCACHED_HOST and MEMCACHED_KEY env vars are required. Please add them to .env")
