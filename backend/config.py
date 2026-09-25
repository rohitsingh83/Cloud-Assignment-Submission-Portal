import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# App settings
PROJECT_NAME = "Cloud-Based Student Assignment Submission & Feedback Portal"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "cloud-assignment-portal-default-dev-secret-key-change-in-prod-2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/assignment_portal.db")

# Cloud Object Storage Driver Simulation
STORAGE_DRIVER = os.getenv("STORAGE_DRIVER", "local")  # 'local', 's3', 'firebase'
STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME", "cloud-assignment-portal-bucket")
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR", str(BASE_DIR / "cloud_storage_bucket"))

# File constraints
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
ALLOWED_EXTENSIONS = [
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,zip,png,jpg,jpeg").split(",")
]
