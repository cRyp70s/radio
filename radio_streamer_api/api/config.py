"""Default configuration

Use env var to override
"""
import os
from datetime import timedelta

REDIS_URL = "redis://redis:6379"
STORAGE_URL = ""
ENV = os.getenv("FLASK_ENV")
DEBUG = ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY") or str(os.urandom(30))
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=3)
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@db:5432/radio_api"
SQLALCHEMY_TRACK_MODIFICATIONS = False
