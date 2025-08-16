from minio import Minio
from minio.error import S3Error
import os
from fastapi import HTTPException
from .config import settings

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = "files"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise HTTPException(
                status_code=500,
                detail=f"MinIO bucket error: {e.message}"
            )

    def upload_file(self, file_object, file_name, content_type):
        try:
            file_size = os.fstat(file_object.fileno()).st_size
            self.client.put_object(
                self.bucket_name,
                file_name,
                file_object,
                file_size,
                content_type=content_type
            )
            return file_name
        except S3Error as e:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {e.message}"
            )

    def get_file(self, file_name):
        try:
            return self.client.get_object(self.bucket_name, file_name)
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise HTTPException(
                    status_code=404,
                    detail="File not found in storage"
                )
            raise HTTPException(
                status_code=500,
                detail=f"File download failed: {e.message}"
            )

    def delete_file(self, file_name):
        try:
            self.client.remove_object(self.bucket_name, file_name)
        except S3Error as e:
            raise HTTPException(
                status_code=500,
                detail=f"File deletion failed: {e.message}"
            )

minio_client = MinioClient()