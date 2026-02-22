from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MovieSimilarity(Base):
    __tablename__ = "movie_similarity"
    __table_args__ = (
        UniqueConstraint("movie_id", "similar_movie_id", name="uq_movie_similarity_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    similar_movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    co_watch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shared_genre_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runtime_distance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserMovieEvent(Base):
    __tablename__ = "user_movie_events"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", "event_type", name="uq_user_movie_event"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
