"""
File storage utility.
Supports local filesystem (dev) and S3-compatible storage (production/Railway).
Controlled by settings.STORAGE_BACKEND = "local" | "s3".
"""
import os
import uuid
from pathlib import Path

from app.core.config import settings


def _generate_filename(original_filename: str) -> str:
    """Prefix with UUID to prevent collisions and path traversal."""
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def save_upload(file_bytes: bytes, original_filename: str, subfolder: str = "uploads") -> str:
    """
    Save an uploaded file and return the storage path/key.

    Returns:
        str: relative path (local) or S3 key (s3 backend)
    """
    if settings.STORAGE_BACKEND == "s3":
        return await _save_to_s3(file_bytes, original_filename, subfolder)
    return await _save_local(file_bytes, original_filename, subfolder)


async def _save_local(file_bytes: bytes, original_filename: str, subfolder: str) -> str:
    import aiofiles

    dest_dir = Path(settings.LOCAL_UPLOAD_DIR) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = _generate_filename(original_filename)
    dest_path = dest_dir / filename

    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(file_bytes)

    return str(dest_path)


async def _save_to_s3(file_bytes: bytes, original_filename: str, subfolder: str) -> str:
    # TODO: implement S3 upload via boto3
    # import boto3
    # s3 = boto3.client("s3", ...)
    # key = f"{subfolder}/{_generate_filename(original_filename)}"
    # s3.put_object(Bucket=settings.AWS_BUCKET_NAME, Key=key, Body=file_bytes)
    # return key
    raise NotImplementedError("S3 storage not yet configured")


def get_public_url(file_path: str) -> str:
    """
    Returns a URL or path suitable for the client to download the file.
    For local: returns the relative path (served via static files or a download endpoint).
    For S3: returns a presigned URL.
    """
    if settings.STORAGE_BACKEND == "s3":
        # TODO: generate presigned URL
        raise NotImplementedError
    return file_path
