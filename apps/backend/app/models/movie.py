from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    runtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[str] = mapped_column(String(10), default="NR")
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
