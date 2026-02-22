from app.workers.celery_app import celery_app


@celery_app.task(name="reservation.expire")
def expire_reservation_task(reservation_id: int) -> dict[str, int]:
    # Placeholder task; expiration logic arrives in reservation milestone.
    return {"reservation_id": reservation_id}
