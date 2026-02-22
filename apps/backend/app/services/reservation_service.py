from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.reservation import Reservation, ReservationSeat, ShowtimeSeatStatus
from app.models.showtime import Showtime


class ReservationService:
    async def expire_overdue_holds(self, session: AsyncSession) -> int:
        now = datetime.now(tz=UTC)
        expired_ids = list(
            (
                await session.execute(
                    select(Reservation.id).where(
                        Reservation.status == "ACTIVE",
                        Reservation.expires_at <= now,
                    )
                )
            ).scalars()
        )
        if not expired_ids:
            return 0

        await session.execute(
            update(Reservation)
            .where(Reservation.id.in_(expired_ids))
            .values(status="EXPIRED")
        )
        await session.execute(
            update(ShowtimeSeatStatus)
            .where(ShowtimeSeatStatus.held_by_reservation_id.in_(expired_ids))
            .values(status="AVAILABLE", held_by_reservation_id=None)
        )
        return len(expired_ids)

    async def create_hold(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        showtime_id: int,
        seat_ids: list[int],
        hold_minutes: int,
    ) -> Reservation:
        unique_seat_ids = sorted(set(seat_ids))
        if not unique_seat_ids:
            raise HTTPException(status_code=400, detail="seat_ids cannot be empty")

        showtime_exists = (
            await session.execute(select(Showtime.id).where(Showtime.id == showtime_id))
        ).scalar_one_or_none()
        if showtime_exists is None:
            raise HTTPException(status_code=404, detail="Showtime not found")

        await self.expire_overdue_holds(session)

        seat_statuses = list(
            (
                await session.execute(
                    select(ShowtimeSeatStatus)
                    .where(
                        ShowtimeSeatStatus.showtime_id == showtime_id,
                        ShowtimeSeatStatus.seat_id.in_(unique_seat_ids),
                    )
                    .with_for_update()
                )
            ).scalars()
        )
        if len(seat_statuses) != len(unique_seat_ids):
            raise HTTPException(status_code=404, detail="One or more seats were not found")

        unavailable_seat_ids = [
            seat_status.seat_id
            for seat_status in seat_statuses
            if seat_status.status != "AVAILABLE"
        ]
        if unavailable_seat_ids:
            unavailable_text = ",".join(str(seat_id) for seat_id in unavailable_seat_ids)
            raise HTTPException(
                status_code=409,
                detail=f"One or more seats are no longer available: {unavailable_text}",
            )

        now = datetime.now(tz=UTC)
        reservation = Reservation(
            user_id=user_id,
            showtime_id=showtime_id,
            status="ACTIVE",
            expires_at=now + timedelta(minutes=hold_minutes),
        )
        session.add(reservation)
        await session.flush()

        session.add_all(
            [
                ReservationSeat(reservation_id=reservation.id, seat_id=seat_id)
                for seat_id in unique_seat_ids
            ]
        )

        for seat_status in seat_statuses:
            seat_status.status = "HELD"
            seat_status.held_by_reservation_id = reservation.id

        await session.flush()
        return reservation

    async def release_hold(
        self,
        session: AsyncSession,
        *,
        reservation: Reservation,
    ) -> None:
        if reservation.status != "ACTIVE":
            return

        reservation.status = "CANCELED"
        await session.execute(
            update(ShowtimeSeatStatus)
            .where(
                ShowtimeSeatStatus.showtime_id == reservation.showtime_id,
                ShowtimeSeatStatus.held_by_reservation_id == reservation.id,
                ShowtimeSeatStatus.status == "HELD",
            )
            .values(status="AVAILABLE", held_by_reservation_id=None)
        )


async def expire_overdue_holds_job() -> int:
    service = ReservationService()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            return await service.expire_overdue_holds(session)
