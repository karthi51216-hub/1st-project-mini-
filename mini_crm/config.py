# import os

# SECRET_KEY = "dev-secret-change-me"

# DB_CONFIG = {
#     "host": "host.docker.internal",
#     "user": "root",
#     "password": "12345",
#     "database": "mini_crm",
# }

# UPLOAD_FOLDER = os.path.join("static", "uploads")
# ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
}