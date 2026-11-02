"""Environment-backed settings (also documented in .env.example)."""
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///asset_verification.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
