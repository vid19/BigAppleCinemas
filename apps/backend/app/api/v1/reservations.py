from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import create_rate_limiter
from app.db.session import get_db_session
from app.models.reservation import Reservation, ReservationSeat
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationRead
from app.services.reservation_service import ReservationService

router = APIRouter()
reservation_service = ReservationService()
reservation_create_rate_limiter = create_rate_limiter(
    key_prefix="reservations:create",
    max_requests=lambda: settings.rate_limit_reservations_create,
    window_seconds=lambda: settings.rate_limit_reservations_window_seconds,
)


def get_current_user_id(x_user_id: int | None = Header(default=None)) -> int:
    if x_user_id is not None and x_user_id < 1:
        raise HTTPException(status_code=400, detail="x-user-id must be greater than zero")
    return x_user_id or 1


async def _get_reservation_read(
    session: AsyncSession,
    reservation_id: int,
    user_id: int,
) -> ReservationRead:
    reservation = (
        await session.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id, Reservation.user_id == user_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")

    seat_ids = list(
        (
            await session.execute(
                select(ReservationSeat.seat_id)
                .where(ReservationSeat.reservation_id == reservation.id)
                .order_by(ReservationSeat.seat_id.asc())
            )
        ).scalars()
    )
    return ReservationRead(
        id=reservation.id,
        user_id=reservation.user_id,
        showtime_id=reservation.showtime_id,
        status=reservation.status,
        expires_at=reservation.expires_at,
        seat_ids=seat_ids,
        created_at=reservation.created_at,
    )


@router.post("", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    payload: ReservationCreate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(reservation_create_rate_limiter),
    user_id: int = Depends(get_current_user_id),
) -> ReservationRead:
    async with session.begin():
        user_exists = (
            await session.execute(select(User.id).where(User.id == user_id))
        ).scalar_one_or_none()
        if user_exists is None:
            raise HTTPException(status_code=404, detail="User not found")

        reservation = await reservation_service.create_hold(
            session,
            user_id=user_id,
            showtime_id=payload.showtime_id,
            seat_ids=payload.seat_ids,
            hold_minutes=settings.reservation_hold_minutes,
        )
        reservation_read = await _get_reservation_read(session, reservation.id, user_id)
    return reservation_read


@router.get("/active", response_model=ReservationRead | None)
async def get_active_reservation(
    showtime_id: int = Query(ge=1),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> ReservationRead | None:
    async with session.begin():
        await reservation_service.expire_overdue_holds(session)
        active_reservation = (
            await session.execute(
                select(Reservation)
                .where(
                    Reservation.user_id == user_id,
                    Reservation.showtime_id == showtime_id,
                    Reservation.status == "ACTIVE",
                )
                .order_by(Reservation.created_at.desc())
                .with_for_update()
            )
        ).scalars().first()
        if active_reservation is None:
            return None
        return await _get_reservation_read(session, active_reservation.id, user_id)


@router.get("/{reservation_id}", response_model=ReservationRead)
async def get_reservation(
    reservation_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> ReservationRead:
    async with session.begin():
        await reservation_service.expire_overdue_holds(session)
        reservation_read = await _get_reservation_read(session, reservation_id, user_id)
    return reservation_read


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> Response:
    async with session.begin():
        await reservation_service.expire_overdue_holds(session)
        reservation = (
            await session.execute(
                select(Reservation)
                .where(Reservation.id == reservation_id, Reservation.user_id == user_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        await reservation_service.release_hold(session, reservation=reservation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
