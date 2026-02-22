from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
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
