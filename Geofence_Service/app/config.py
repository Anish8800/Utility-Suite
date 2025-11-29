import os
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EVENT_DEBOUNCE_SECONDS = int(os.getenv("EVENT_DEBOUNCE_SECONDS", "2"))
ZONES_CONFIG_PATH = os.getenv("ZONES_CONFIG_PATH", "configs/zones.json")