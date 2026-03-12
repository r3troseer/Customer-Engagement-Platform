"""
File storage utility.
Supports local filesystem (dev) and S3-compatible storage (Railway Bucket / AWS S3).
Controlled by settings.STORAGE_BACKEND = "local" | "s3".
"""
import uuid
from pathlib import Path

from app.core.config import settings


def _generate_key(original_filename: str, subfolder: str) -> str:
    """UUID-prefixed key — prevents collisions and path traversal."""
    ext = Path(original_filename).suffix.lower()
    return f"{subfolder}/{uuid.uuid4().hex}{ext}"


def _s3_client():
    import boto3

    kwargs = dict(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


async def save_upload(file_bytes: bytes, original_filename: str, subfolder: str = "uploads") -> str:
    """
    Save an uploaded file and return the storage key/path.

    Returns:
        str: S3 object key (s3 backend) or relative local path (local backend)
    """
    if settings.STORAGE_BACKEND == "s3":
        return await _save_to_s3(file_bytes, original_filename, subfolder)
    return await _save_local(file_bytes, original_filename, subfolder)


async def _save_local(file_bytes: bytes, original_filename: str, subfolder: str) -> str:
    import aiofiles

    dest_dir = Path(settings.LOCAL_UPLOAD_DIR) / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    key = _generate_key(original_filename, subfolder)
    dest_path = Path(settings.LOCAL_UPLOAD_DIR) / key
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(file_bytes)

    return key


async def _save_to_s3(file_bytes: bytes, original_filename: str, subfolder: str) -> str:
    import asyncio
    from functools import partial

    key = _generate_key(original_filename, subfolder)
    client = _s3_client()

    # boto3 is sync — run in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        partial(
            client.put_object,
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
        ),
    )
    return key


def get_download_url(key: str, expires_in: int = 3600) -> str:
    """
    Returns a URL for the client to download the file.
    Local: returns the key as-is (served via a download endpoint).
    S3: returns a presigned URL valid for `expires_in` seconds (default 1 hour).
    """
    if settings.STORAGE_BACKEND == "s3":
        client = _s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    return key
