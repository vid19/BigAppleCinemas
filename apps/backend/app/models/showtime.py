from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Theater(Base):
    __tablename__ = "theaters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)


class Auditorium(Base):
    __tablename__ = "auditoriums"

    id: Mapped[int] = mapped_column(primary_key=True)
    theater_id: Mapped[int] = mapped_column(ForeignKey("theaters.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    seatmap_id: Mapped[int | None] = mapped_column(ForeignKey("seat_maps.id"), nullable=True)


class SeatMap(Base):
    __tablename__ = "seat_maps"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    layout_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("auditorium_id", "seat_code", name="uq_auditorium_seat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    auditorium_id: Mapped[int] = mapped_column(ForeignKey("auditoriums.id"), nullable=False)
    seat_code: Mapped[str] = mapped_column(String(10), nullable=False)
    row_label: Mapped[str] = mapped_column(String(10), nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_type: Mapped[str] = mapped_column(String(30), nullable=False, default="STANDARD")


class Showtime(Base):
    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    auditorium_id: Mapped[int] = mapped_column(ForeignKey("auditoriums.id"), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="SCHEDULED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
