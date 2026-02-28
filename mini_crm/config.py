import os

SECRET_KEY = "dev-secret-change-me"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345",
    "database": "mini_crm",
}

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}