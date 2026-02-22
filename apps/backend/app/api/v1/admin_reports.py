from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_user
from app.core.metrics import get_metric_value
from app.db.session import get_db_session
from app.models.movie import Movie
from app.models.order import Order, Ticket
from app.models.reservation import Reservation, ShowtimeSeatStatus
from app.models.showtime import Auditorium, Showtime, Theater
from app.schemas.portal import AdminSalesReportResponse, AdminShowtimeSalesItem

router = APIRouter(dependencies=[Depends(require_admin_user)])


@router.get("/sales", response_model=AdminSalesReportResponse)
async def sales_report(
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session),
) -> AdminSalesReportResponse:
    paid_orders = (
        await session.execute(select(func.count(Order.id)).where(Order.status == "PAID"))
    ).scalar_one()
    gross_revenue_cents = (
        await session.execute(
            select(func.coalesce(func.sum(Order.total_cents), 0)).where(Order.status == "PAID")
        )
    ).scalar_one()
    tickets_sold = (
        await session.execute(
            select(func.count(Ticket.id))
            .join(Order, Order.id == Ticket.order_id)
            .where(Order.status == "PAID")
        )
    ).scalar_one()
    active_holds = (
        await session.execute(
            select(func.count(Reservation.id)).where(Reservation.status == "ACTIVE")
        )
    ).scalar_one()

    sold_subquery = (
        select(
            ShowtimeSeatStatus.showtime_id.label("showtime_id"),
            func.count(ShowtimeSeatStatus.id).label("sold_seats"),
        )
        .where(ShowtimeSeatStatus.status == "SOLD")
        .group_by(ShowtimeSeatStatus.showtime_id)
        .subquery()
    )
    capacity_subquery = (
        select(
            ShowtimeSeatStatus.showtime_id.label("showtime_id"),
            func.count(ShowtimeSeatStatus.id).label("capacity"),
        )
        .group_by(ShowtimeSeatStatus.showtime_id)
        .subquery()
    )
    stmt = (
        select(
            Showtime.id.label("showtime_id"),
            Movie.title.label("movie_title"),
            Theater.name.label("theater_name"),
            Showtime.starts_at,
            func.coalesce(sold_subquery.c.sold_seats, 0).label("sold_seats"),
            func.coalesce(capacity_subquery.c.capacity, 0).label("capacity"),
            case(
                (func.coalesce(capacity_subquery.c.capacity, 0) == 0, 0.0),
                else_=(
                    func.coalesce(sold_subquery.c.sold_seats, 0)
                    * 100.0
                    / capacity_subquery.c.capacity
                ),
            ).label("occupancy_percent"),
        )
        .join(Movie, Movie.id == Showtime.movie_id)
        .join(Auditorium, Auditorium.id == Showtime.auditorium_id)
        .join(Theater, Theater.id == Auditorium.theater_id)
        .outerjoin(sold_subquery, sold_subquery.c.showtime_id == Showtime.id)
        .outerjoin(capacity_subquery, capacity_subquery.c.showtime_id == Showtime.id)
        .order_by(Showtime.starts_at.desc())
        .limit(limit)
    )
    showtime_rows = (await session.execute(stmt)).mappings().all()
    showtimes = []
    for row in showtime_rows:
        showtimes.append(
            AdminShowtimeSalesItem(
                showtime_id=row["showtime_id"],
                movie_title=row["movie_title"],
                theater_name=row["theater_name"],
                starts_at=row["starts_at"],
                sold_seats=row["sold_seats"],
                capacity=row["capacity"],
                occupancy_percent=round(float(row["occupancy_percent"] or 0.0), 2),
            )
        )

    return AdminSalesReportResponse(
        paid_orders=paid_orders,
        gross_revenue_cents=gross_revenue_cents,
        tickets_sold=tickets_sold,
        active_holds=active_holds,
        showtimes=showtimes,
        recommendation_impressions=get_metric_value("recommendation_impression_total"),
        recommendation_clicks=get_metric_value("recommendation_click_total"),
        recommendation_saved=get_metric_value("recommendation_save_total"),
        recommendation_hidden=get_metric_value("recommendation_hide_total"),
        recommendation_ctr_percent=round(
            (
                get_metric_value("recommendation_click_total")
                / max(1, get_metric_value("recommendation_impression_total"))
            )
            * 100,
            2,
        ),
        recommendation_save_rate_percent=round(
            (
                get_metric_value("recommendation_save_total")
                / max(1, get_metric_value("recommendation_impression_total"))
            )
            * 100,
            2,
        ),
        recommendation_hide_rate_percent=round(
            (
                get_metric_value("recommendation_hide_total")
                / max(1, get_metric_value("recommendation_impression_total"))
            )
            * 100,
            2,
        ),
    )
