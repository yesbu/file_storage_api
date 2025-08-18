from celery import Celery
from src.app.config import settings

celery_app = Celery(
    'filevault',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['src.app.files.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

