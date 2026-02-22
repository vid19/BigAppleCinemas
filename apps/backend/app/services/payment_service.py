from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import delete_cache_prefix
from app.models.order import Order, Ticket
from app.models.reservation import Reservation, ReservationSeat, ShowtimeSeatStatus
from app.models.showtime import Seat
from app.schemas.payment import CheckoutFinalizeRead, CheckoutSessionRead, TicketRead
from app.services.reservation_service import ReservationService

SEAT_TYPE_PRICE_CENTS = {
    "STANDARD": 1500,
    "PREMIUM": 2000,
    "VIP": 2600,
}


def _seat_price_cents(seat_type: str) -> int:
    return SEAT_TYPE_PRICE_CENTS.get(seat_type.upper(), 1500)


class PaymentService:
    def __init__(self) -> None:
        self._reservation_service = ReservationService()

    async def create_checkout_session(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        reservation_id: int,
        provider: str,
    ) -> CheckoutSessionRead:
        await self._reservation_service.expire_overdue_holds(session)

        reservation = (
            await session.execute(
                select(Reservation)
                .where(Reservation.id == reservation_id, Reservation.user_id == user_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        if reservation.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="Reservation is not active")
        if reservation.expires_at <= datetime.now(tz=UTC):
            raise HTTPException(status_code=409, detail="Reservation has expired")

        existing_order = (
            await session.execute(
                select(Order).where(Order.reservation_id == reservation.id).with_for_update()
            )
        ).scalar_one_or_none()
        if existing_order is not None:
            return CheckoutSessionRead(
                order_id=existing_order.id,
                reservation_id=existing_order.reservation_id,
                provider=existing_order.provider,
                provider_session_id=existing_order.provider_session_id or "",
                status=existing_order.status,
                total_cents=existing_order.total_cents,
                currency=existing_order.currency,
                checkout_url=(
                    f"/checkout/processing?order_id={existing_order.id}"
                    f"&session_id={existing_order.provider_session_id}"
                ),
                created_at=existing_order.created_at,
            )

        seat_rows = (
            await session.execute(
                select(Seat.id, Seat.seat_type)
                .join(ReservationSeat, ReservationSeat.seat_id == Seat.id)
                .where(ReservationSeat.reservation_id == reservation.id)
                .order_by(Seat.id.asc())
            )
        ).all()
        if not seat_rows:
            raise HTTPException(status_code=400, detail="Reservation has no seats")

        total_cents = sum(_seat_price_cents(seat_type) for _, seat_type in seat_rows)
        provider_session_id = f"cs_mock_{uuid4().hex}"
        order = Order(
            user_id=user_id,
            showtime_id=reservation.showtime_id,
            reservation_id=reservation.id,
            status="PENDING",
            total_cents=total_cents,
            currency="USD",
            provider=provider,
            provider_session_id=provider_session_id,
        )
        session.add(order)
        await session.flush()
        return CheckoutSessionRead(
            order_id=order.id,
            reservation_id=order.reservation_id,
            provider=order.provider,
            provider_session_id=provider_session_id,
            status=order.status,
            total_cents=order.total_cents,
            currency=order.currency,
            checkout_url=f"/checkout/processing?order_id={order.id}&session_id={provider_session_id}",
            created_at=order.created_at,
        )

    async def finalize_paid_order(
        self,
        session: AsyncSession,
        *,
        order: Order,
    ) -> CheckoutFinalizeRead:
        await self._reservation_service.expire_overdue_holds(session)

        reservation = (
            await session.execute(
                select(Reservation).where(Reservation.id == order.reservation_id).with_for_update()
            )
        ).scalar_one_or_none()
        if reservation is None:
            raise HTTPException(status_code=404, detail="Order reservation not found")

        if order.status == "PAID":
            return await self._finalize_payload(session, order.id, order.status)

        if reservation.status != "ACTIVE":
            order.status = "FAILED"
            return await self._finalize_payload(session, order.id, order.status)

        reservation_seat_ids = list(
            (
                await session.execute(
                    select(ReservationSeat.seat_id)
                    .where(ReservationSeat.reservation_id == reservation.id)
                    .order_by(ReservationSeat.seat_id.asc())
                )
            ).scalars()
        )
        if not reservation_seat_ids:
            order.status = "FAILED"
            return await self._finalize_payload(session, order.id, order.status)

        held_rows = list(
            (
                await session.execute(
                    select(ShowtimeSeatStatus)
                    .where(
                        ShowtimeSeatStatus.showtime_id == reservation.showtime_id,
                        ShowtimeSeatStatus.seat_id.in_(reservation_seat_ids),
                    )
                    .with_for_update()
                )
            ).scalars()
        )
        if len(held_rows) != len(reservation_seat_ids):
            order.status = "FAILED"
            return await self._finalize_payload(session, order.id, order.status)

        for seat_status in held_rows:
            if (
                seat_status.status != "HELD"
                or seat_status.held_by_reservation_id != reservation.id
            ):
                order.status = "FAILED"
                return await self._finalize_payload(session, order.id, order.status)

        await session.execute(
            update(ShowtimeSeatStatus)
            .where(
                ShowtimeSeatStatus.showtime_id == reservation.showtime_id,
                ShowtimeSeatStatus.seat_id.in_(reservation_seat_ids),
                ShowtimeSeatStatus.held_by_reservation_id == reservation.id,
            )
            .values(status="SOLD", held_by_reservation_id=None)
        )
        reservation.status = "COMPLETED"
        order.status = "PAID"
        await delete_cache_prefix(f"recommendations:{order.user_id}:")

        existing_ticket_seat_ids = set(
            (
                await session.execute(select(Ticket.seat_id).where(Ticket.order_id == order.id))
            ).scalars()
        )
        missing_seat_ids = [
            seat_id
            for seat_id in reservation_seat_ids
            if seat_id not in existing_ticket_seat_ids
        ]
        if missing_seat_ids:
            session.add_all(
                [
                    Ticket(
                        order_id=order.id,
                        seat_id=seat_id,
                        qr_token=f"tkt_{uuid4().hex}",
                        status="VALID",
                    )
                    for seat_id in missing_seat_ids
                ]
            )
            await session.flush()

        return await self._finalize_payload(session, order.id, order.status)

    async def get_order_for_user(
        self,
        session: AsyncSession,
        *,
        order_id: int,
        user_id: int,
    ) -> Order:
        order = (
            await session.execute(
                select(Order)
                .where(Order.id == order_id, Order.user_id == user_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def get_order_by_provider_session(
        self,
        session: AsyncSession,
        *,
        provider_session_id: str,
    ) -> Order:
        order = (
            await session.execute(
                select(Order)
                .where(Order.provider_session_id == provider_session_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def get_order_by_id(self, session: AsyncSession, *, order_id: int) -> Order:
        order = (
            await session.execute(select(Order).where(Order.id == order_id).with_for_update())
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def _finalize_payload(
        self,
        session: AsyncSession,
        order_id: int,
        order_status: str,
    ) -> CheckoutFinalizeRead:
        ticket_rows = (
            await session.execute(
                select(Ticket).where(Ticket.order_id == order_id).order_by(Ticket.id.asc())
            )
        ).scalars().all()
        tickets = [
            TicketRead(
                id=ticket.id,
                seat_id=ticket.seat_id,
                qr_token=ticket.qr_token,
                status=ticket.status,
            )
            for ticket in ticket_rows
        ]
        return CheckoutFinalizeRead(
            order_id=order_id,
            order_status=order_status,
            ticket_count=len(tickets),
            tickets=tickets,
        )
