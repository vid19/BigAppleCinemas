from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.movie import Movie
from app.models.showtime import Auditorium, Showtime, Theater
from app.services.seat_inventory import (
    ensure_auditorium_seat_inventory,
    sync_showtime_seat_statuses,
)


async def bootstrap_local_data() -> None:
    """Create tables and seed demo catalog + seat inventory for local development."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        theater = (
            await session.execute(select(Theater).order_by(Theater.id.asc()))
        ).scalars().first()
        if theater is None:
            theater = Theater(
                name="Big Apple Cinemas - Midtown",
                address="123 Broadway",
                city="New York",
                timezone="America/New_York",
            )
            session.add(theater)
            await session.flush()

        auditorium = (
            await session.execute(
                select(Auditorium)
                .where(Auditorium.theater_id == theater.id)
                .order_by(Auditorium.id.asc())
            )
        ).scalars().first()
        if auditorium is None:
            auditorium = Auditorium(
                theater_id=theater.id,
                name="Auditorium 1",
                seatmap_id=None,
            )
            session.add(auditorium)
            await session.flush()

        movie_exists = (await session.execute(select(Movie.id).limit(1))).scalar_one_or_none()
        if movie_exists is None:
            movies = [
                Movie(
                    title="Skyline Heist",
                    description="An elite crew attempts a high-stakes heist above Manhattan.",
                    runtime_minutes=126,
                    rating="PG-13",
                    release_date=datetime(2026, 2, 6, tzinfo=UTC).date(),
                    poster_url="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba",
                    metadata_json={"genre": ["Action", "Thriller"]},
                ),
                Movie(
                    title="Midnight Orbit",
                    description="A sci-fi thriller about a rescue mission at the edge of orbit.",
                    runtime_minutes=112,
                    rating="PG-13",
                    release_date=datetime(2026, 1, 24, tzinfo=UTC).date(),
                    poster_url="https://images.unsplash.com/photo-1478720568477-152d9b164e26",
                    metadata_json={"genre": ["Sci-Fi", "Drama"]},
                ),
                Movie(
                    title="The Last Encore",
                    description="A drama following a retired musician's return to the spotlight.",
                    runtime_minutes=104,
                    rating="PG",
                    release_date=datetime(2025, 12, 18, tzinfo=UTC).date(),
                    poster_url="https://images.unsplash.com/photo-1517602302552-471fe67acf66",
                    metadata_json={"genre": ["Drama"]},
                ),
            ]
            session.add_all(movies)
            await session.flush()

            now = datetime.now(tz=UTC).replace(minute=0, second=0, microsecond=0)
            for index, movie in enumerate(movies):
                starts_at = now + timedelta(hours=(index + 1) * 2)
                session.add(
                    Showtime(
                        movie_id=movie.id,
                        auditorium_id=auditorium.id,
                        starts_at=starts_at,
                        ends_at=starts_at + timedelta(minutes=movie.runtime_minutes + 20),
                        status="SCHEDULED",
                    )
                )

        all_auditoriums = (await session.execute(select(Auditorium))).scalars().all()
        for item in all_auditoriums:
            await ensure_auditorium_seat_inventory(session, item)

        all_showtimes = (await session.execute(select(Showtime))).scalars().all()
        for showtime in all_showtimes:
            await sync_showtime_seat_statuses(session, showtime)

        await session.commit()
