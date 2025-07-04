# backend/src/config.py
# Environment variable loading and basic configuration

import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key") # TODO: Generate a strong secret key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

settings = Settings()
