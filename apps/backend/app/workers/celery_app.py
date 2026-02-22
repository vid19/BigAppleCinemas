from celery import Celery

from app.core.config import settings

celery_app = Celery("bigapplecinemas", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app.workers"])
