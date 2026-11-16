"""Application configuration and environment loading."""

from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parent


def load_config() -> dict[str, object]:
    """Load settings from backend/.env and apply development defaults."""
    load_dotenv(BACKEND_ROOT / ".env")

    image_limit = 8 * 1024 * 1024
    origins = os.environ.get(
        "CORS_ORIGINS",
        "https://brian-kiprotich.netlify.app/",
    )

    return {
        "SECRET_KEY": os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32),
        "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD", ""),
        "TOKEN_MAX_AGE": int(timedelta(hours=8).total_seconds()),
        "TOKEN_SALT": "portfolio-admin-v1",
        "DATA_FILE": Path(os.environ.get("PORTFOLIO_DATA_FILE", BACKEND_ROOT / "data" / "content.json")),
        "UPLOAD_DIR": Path(os.environ.get("PORTFOLIO_UPLOAD_DIR", BACKEND_ROOT / "uploads")),
        "MAX_IMAGE_BYTES": image_limit,
        "MAX_CONTENT_LENGTH": image_limit + 64 * 1024,
        "ALLOWED_IMAGE_TYPES": {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        },
        "CORS_ORIGINS": [origin.strip() for origin in origins.split(",") if origin.strip()],
    }
