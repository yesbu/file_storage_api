from celery import shared_task
from sqlalchemy import select
from ..database import SessionLocal
from .models import File, FileMetadata
from .utils.metadata_extractors import extract_pdf_meta, extract_office_meta
from ..storage.s3 import s3_client
from ..config import settings
@shared_task
def extract_metadata_task(file_id: int):
    import asyncio
    asyncio.run(_extract_metadata_async(file_id))
async def _extract_metadata_async(file_id: int):
    async with SessionLocal() as session:
        res = await session.execute(select(File).where(File.id == file_id))
        f = res.scalar_one_or_none()
        if not f:
            return
        obj = s3_client().get_object(Bucket=settings.s3_bucket, Key=f.s3_key)
        data = obj["Body"].read()
        if f.content_type == "application/pdf":
            meta = extract_pdf_meta(data)
        elif f.content_type in {"application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
            meta = extract_office_meta(data, f.filename)
        else:
            meta = {"type": "unknown"}
        existing = await session.execute(select(FileMetadata).where(FileMetadata.file_id == f.id))
        m = existing.scalar_one_or_none()
        if m:
            m.raw = meta
        else:
            m = FileMetadata(file_id=f.id, raw=meta)
            session.add(m)
        await session.commit()
