from minio import Minio
from minio.error import S3Error
import logging
from ..config import settings

logger = logging.getLogger(__name__)

def get_minio_client():
    return Minio(
        endpoint=settings.minio_endpoint.split('://')[-1],
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )

def ensure_bucket():
    try:
        client = get_minio_client()
        if not client.bucket_exists(settings.minio_bucket_files):
            client.make_bucket(settings.minio_bucket_files)
            logger.info(f"Created MinIO bucket: {settings.minio_bucket_files}")
    except S3Error as e:
        logger.error(f"MinIO bucket operation failed: {e}")
        raise


def put_object(key: str, content: bytes, content_type: str) -> None:
    client = get_minio_client()

    # Конвертируем bytes в BytesIO
    from io import BytesIO
    data = BytesIO(content)
    length = len(content)

    client.put_object(
        settings.minio_bucket_files,
        key,
        data,
        length,
        content_type=content_type
    )


def get_presigned_url(key: str, expires: int = 3600) -> str:
    try:
        ensure_bucket()
        client = get_minio_client()
        return client.presigned_get_object(
            bucket_name=settings.minio_bucket_files,
            object_name=key,
            expires=expires
        )
    except Exception as e:
        logger.error(f"MinIO presigned URL generation failed: {e}")
        raise
