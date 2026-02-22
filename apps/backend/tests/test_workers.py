from app.workers.celery_app import celery_app


def test_celery_beat_schedule_includes_similarity_rebuild() -> None:
    beat_schedule = celery_app.conf.beat_schedule
    assert "expire-overdue-reservations" in beat_schedule
    assert "rebuild-movie-similarity" in beat_schedule
