from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("bigapplecinemas", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(["app.workers"])
celery_app.conf.beat_schedule = {
    "expire-overdue-reservations": {
        "task": "reservation.expire_overdue",
        "schedule": max(5, settings.reservation_expiry_sweep_seconds),
    },
    "rebuild-movie-similarity": {
        "task": "recommendation.rebuild_movie_similarity",
        "schedule": crontab(
            minute=settings.recommendation_rebuild_minute_utc,
            hour=settings.recommendation_rebuild_hour_utc,
        ),
    }
}
