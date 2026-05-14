import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DATABASE_URL = os.getenv("LAUNCH_ENGINE_DATABASE_URL") or os.getenv("DATABASE_URL")
    META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "1034387189758630")
    META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
    META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")
    META_PAGE_ID = os.getenv("META_PAGE_ID", "")

    # R2 / S3
    R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_ENDPOINT = os.getenv("R2_ENDPOINT")
    R2_BUCKET = os.getenv("R2_BUCKET")
    R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")