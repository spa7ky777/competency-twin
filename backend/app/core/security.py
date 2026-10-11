import re
import uuid
from pathlib import Path

from app.config import get_settings
from app.core.errors import AppError

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(original: str) -> str:
    name = Path(original.replace("\\", "/")).name
    name = SAFE_NAME.sub("_", name).strip("._") or "file"
    return name[:180]


def stored_name(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def validate_upload(filename: str, size: int, content_type: str | None = None) -> str:
    settings = get_settings()
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in settings.allowed_ext_set:
        raise AppError("INVALID_FILE_TYPE", f"File type .{ext} is not allowed.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size > max_bytes:
        raise AppError("FILE_TOO_LARGE", f"File exceeds {settings.max_upload_mb} MB.")
    if size == 0:
        raise AppError("EMPTY_FILE", "The uploaded file is empty.")
    return ext
