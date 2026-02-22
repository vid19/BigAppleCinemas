from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReservationSeat(Base):
    __tablename__ = "reservation_seats"
    __table_args__ = (UniqueConstraint("reservation_id", "seat_id", name="uq_reservation_seat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("reservations.id"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), nullable=False)


class ShowtimeSeatStatus(Base):
    __tablename__ = "showtime_seat_status"
    __table_args__ = (UniqueConstraint("showtime_id", "seat_id", name="uq_showtime_seat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), nullable=False, index=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE", nullable=False, index=True)
    held_by_reservation_id: Mapped[int | None] = mapped_column(
        ForeignKey("reservations.id"),
        nullable=True,
    )
