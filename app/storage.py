import os, uuid, mimetypes
from flask import current_app
import boto3

def _safe_name(filename: str) -> str:
    filename = os.path.basename(filename or "file")
    return filename.replace("..", "")

def save_upload(file_storage, subdir: str) -> dict:
    cfg = current_app.config
    filename = _safe_name(file_storage.filename)
    mime = file_storage.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    key = f"{subdir}/{uuid.uuid4().hex}_{filename}"

    backend = (cfg.get("STORAGE_BACKEND") or "local").lower()
    if backend == "s3":
        return _save_s3(file_storage, key, filename, mime)
    return _save_local(file_storage, key, filename, mime)

def _save_local(file_storage, key: str, filename: str, mime: str) -> dict:
    cfg = current_app.config
    full_path = os.path.join(cfg["STORAGE_DIR"], key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    file_storage.save(full_path)
    return {"url":"", "storage_key": full_path, "filename": filename, "mime": mime, "key": key}

def _save_s3(file_storage, key: str, filename: str, mime: str) -> dict:
    cfg = current_app.config
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg.get("S3_ENDPOINT_URL") or None,
        aws_access_key_id=cfg.get("S3_ACCESS_KEY_ID") or None,
        aws_secret_access_key=cfg.get("S3_SECRET_ACCESS_KEY") or None,
        region_name=cfg.get("S3_REGION") or None,
    )
    bucket = cfg["S3_BUCKET"]
    s3.upload_fileobj(file_storage.stream, bucket, key, ExtraArgs={"ContentType": mime})
    public_base = cfg.get("S3_PUBLIC_BASE_URL") or ""
    url = f"{public_base.rstrip('/')}/{key}" if public_base else f"s3://{bucket}/{key}"
    return {"url": url, "storage_key": key, "filename": filename, "mime": mime, "key": key}
