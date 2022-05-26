"""Default configuration

Use env var to override
"""
import os
from datetime import timedelta

REDIS_URL = "redis://localhost:6379"
STORAGE_URL = ""
ENV = os.getenv("FLASK_ENV")
DEBUG = ENV == "development"
SECRET_KEY = os.getenv("SECRET_KEY") or "nmjfyfr5yyy3345y())!!!!ui6ARGHEYR43322767"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=3)
SQLALCHEMY_DATABASE_URI = "sqlite:///db.db"#os.getenv("DATABASE_URI")
SQLALCHEMY_TRACK_MODIFICATIONS = False
