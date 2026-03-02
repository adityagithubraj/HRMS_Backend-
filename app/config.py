import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    PROJECT_NAME: str = "HRMS Lite API"
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/hrms_lite")
    DATABASE_NAME: str = os.getenv("MONGODB_DB_NAME", "hrms_lite")
    API_V1_PREFIX: str = "/api"


@lru_cache
def get_settings() -> Settings:
    return Settings()

