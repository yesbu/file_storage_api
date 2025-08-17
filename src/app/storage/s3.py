import boto3
from botocore.client import Config as BotoConfig
from ..config import settings
def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=BotoConfig(signature_version="s3v4"),
        use_ssl=settings.s3_secure,
    )
def put_object(key: str, data: bytes, content_type: str):
    s3_client().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)
def get_presigned_url(key: str, expires: int = 3600) -> str:
    return s3_client().generate_presigned_url("get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=expires)
