import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///password_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_AGE = timedelta(days=7).total_seconds()

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
