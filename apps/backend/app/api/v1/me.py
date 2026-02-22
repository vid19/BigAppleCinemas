from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db_session
from app.models.movie import Movie
from app.models.order import Order, Ticket
from app.models.showtime import Auditorium, Seat, Showtime, Theater
from app.schemas.portal import (
    MyOrderItem,
    MyOrderListResponse,
    MyTicketItem,
    MyTicketListResponse,
)

router = APIRouter()


@router.get("/tickets", response_model=MyTicketListResponse)
async def list_my_tickets(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> MyTicketListResponse:
    stmt = (
        select(
            Ticket.id.label("ticket_id"),
            Ticket.order_id,
            Ticket.qr_token,
            Ticket.status.label("ticket_status"),
            Seat.seat_code,
            Seat.seat_type,
            Movie.title.label("movie_title"),
            Theater.name.label("theater_name"),
            Showtime.id.label("showtime_id"),
            Showtime.starts_at.label("showtime_starts_at"),
            Ticket.used_at,
            Ticket.created_at,
        )
        .join(Order, Order.id == Ticket.order_id)
        .join(Seat, Seat.id == Ticket.seat_id)
        .join(Showtime, Showtime.id == Order.showtime_id)
        .join(Movie, Movie.id == Showtime.movie_id)
        .join(Auditorium, Auditorium.id == Showtime.auditorium_id)
        .join(Theater, Theater.id == Auditorium.theater_id)
        .where(Order.user_id == user_id)
        .order_by(Showtime.starts_at.desc(), Ticket.id.desc())
    )
    rows = (await session.execute(stmt)).mappings().all()
    items = [MyTicketItem.model_validate(row) for row in rows]
    return MyTicketListResponse(items=items, total=len(items))


@router.get("/orders", response_model=MyOrderListResponse)
async def list_my_orders(
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> MyOrderListResponse:
    ticket_count_subquery = (
        select(Ticket.order_id, func.count(Ticket.id).label("ticket_count"))
        .group_by(Ticket.order_id)
        .subquery()
    )
    stmt = (
        select(
            Order.id.label("order_id"),
            Order.reservation_id,
            Order.showtime_id,
            Order.status,
            Order.total_cents,
            Order.currency,
            Order.provider,
            func.coalesce(ticket_count_subquery.c.ticket_count, 0).label("ticket_count"),
            Order.created_at,
        )
        .outerjoin(ticket_count_subquery, ticket_count_subquery.c.order_id == Order.id)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    rows = (await session.execute(stmt)).mappings().all()
    items = [MyOrderItem.model_validate(row) for row in rows]
    return MyOrderListResponse(items=items, total=len(items))
