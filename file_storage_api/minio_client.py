from minio import Minio
from minio.error import S3Error
import os

from dotenv import load_dotenv
load_dotenv()

minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE").lower() == "true"
)

# Создание bucket по умолчанию (если не существует)
try:
    if not minio_client.bucket_exists("files"):
        minio_client.make_bucket("files")
except S3Error as exc:
    print("Error creating bucket:", exc)