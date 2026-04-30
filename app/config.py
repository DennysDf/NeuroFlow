import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://neuroflow:neuroflow@localhost:5432/neuroflow"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8h
    RATELIMIT_STORAGE_URI = "memory://"


class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL", "sqlite:///:memory:"
    )
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"


def get_config(name: str | None = None) -> type[BaseConfig]:
    name = (name or os.environ.get("FLASK_ENV") or "development").lower()
    return {
        "development": DevConfig,
        "production": ProdConfig,
        "testing": TestConfig,
    }.get(name, DevConfig)
