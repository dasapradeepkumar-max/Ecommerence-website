import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "techtrend-super-secret-ecom-key-2026")

    # Database Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecommerce_db")

    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
    OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    OTP_RESEND_LIMIT = int(os.getenv("OTP_RESEND_LIMIT", "3"))
    ALLOW_CONSOLE_OTP = os.getenv("ALLOW_CONSOLE_OTP", "true").lower() == "true"

    # Business Rules
    DEFAULT_DELIVERY_FEE = float(os.getenv("DEFAULT_DELIVERY_FEE", "49.0"))
    FREE_DELIVERY_MIN_TOTAL = float(os.getenv("FREE_DELIVERY_MIN_TOTAL", "999.0"))

    # Folder Paths
    TEMPLATE_FOLDER = BASE_DIR / "frontend" / "templates"
    STATIC_FOLDER = BASE_DIR / "frontend" / "static"
    UPLOAD_FOLDER = BASE_DIR / "frontend" / "static" / "images" / "uploads"
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "svg"}
