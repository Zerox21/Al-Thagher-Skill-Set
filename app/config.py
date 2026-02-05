import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    APP_VERSION = os.getenv("APP_VERSION", "v1")

    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_DIR = os.getenv("STORAGE_DIR", "instance/storage")
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", "instance/storage/uploads")
    MEDIA_DIR = os.getenv("MEDIA_DIR", "instance/storage/media")
    REPORTS_DIR = os.getenv("REPORTS_DIR", "instance/storage/reports")

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(50 * 1024 * 1024)))

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_FROM = os.getenv("SMTP_FROM", "")

    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL", "")
