import asyncio
import logging

from app.services.reservation_service import expire_overdue_holds_job
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="reservation.expire_overdue")
def expire_overdue_reservations_task() -> dict[str, int]:
    released_count = asyncio.run(expire_overdue_holds_job())
    if released_count > 0:
        logger.info("Expired %s overdue reservations", released_count)
    return {"expired_reservations": released_count}
