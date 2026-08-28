"""
backend/app/services/storage.py
S3 presigned URL generation for profile photo uploads.
"""
import uuid
import boto3
from botocore.config import Config

from app.core.config import settings

_s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
    config=Config(signature_version="s3v4"),
)


def generate_upload_url(user_id: str, file_extension: str = "jpg", expires_in: int = 300) -> dict:
    key = f"profile-photos/{user_id}/{uuid.uuid4()}.{file_extension}"
    upload_url = _s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key, "ContentType": f"image/{file_extension}"},
        ExpiresIn=expires_in,
    )
    file_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
    return {"upload_url": upload_url, "file_url": file_url}
