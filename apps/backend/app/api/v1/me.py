from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.db.session import get_db_session
from app.models.movie import Movie
from app.models.order import Order, Ticket
from app.models.showtime import Auditorium, Seat, Showtime, Theater
from app.schemas.portal import (
    MovieRecommendationItem,
    MovieRecommendationResponse,
    MyOrderItem,
    MyOrderListResponse,
    MyTicketItem,
    MyTicketListResponse,
)

router = APIRouter()


def _extract_genres(metadata_json: dict | None) -> list[str]:
    if not isinstance(metadata_json, dict):
        return []
    genres = metadata_json.get("genre")
    if not isinstance(genres, list):
        return []
    normalized = []
    for genre in genres:
        if isinstance(genre, str) and genre.strip():
            normalized.append(genre.strip())
    return normalized


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


@router.get("/recommendations", response_model=MovieRecommendationResponse)
async def list_my_recommendations(
    limit: int = Query(default=8, ge=1, le=20),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> MovieRecommendationResponse:
    now = datetime.now(tz=UTC)

    watch_history_stmt = (
        select(
            Movie.id.label("movie_id"),
            Movie.rating.label("rating"),
            Movie.metadata_json.label("metadata_json"),
            func.count(Ticket.id).label("watch_count"),
        )
        .join(Showtime, Showtime.movie_id == Movie.id)
        .join(Order, Order.showtime_id == Showtime.id)
        .join(Ticket, Ticket.order_id == Order.id)
        .where(
            Order.user_id == user_id,
            Order.status == "PAID",
        )
        .group_by(Movie.id, Movie.rating, Movie.metadata_json)
    )
    watch_history_rows = (await session.execute(watch_history_stmt)).mappings().all()

    watched_movie_ids = {int(row["movie_id"]) for row in watch_history_rows}
    genre_weights: defaultdict[str, float] = defaultdict(float)
    rating_weights: defaultdict[str, float] = defaultdict(float)
    for row in watch_history_rows:
        weight = float(row["watch_count"] or 1)
        rating = str(row["rating"] or "").strip()
        if rating:
            rating_weights[rating] += weight
        for genre in _extract_genres(row["metadata_json"]):
            genre_weights[genre.lower()] += weight

    upcoming_showtimes_subquery = (
        select(
            Showtime.movie_id.label("movie_id"),
            func.min(Showtime.starts_at).label("next_showtime_starts_at"),
        )
        .where(
            Showtime.starts_at >= now,
            Showtime.status == "SCHEDULED",
        )
        .group_by(Showtime.movie_id)
        .subquery()
    )
    trending_sales_subquery = (
        select(
            Showtime.movie_id.label("movie_id"),
            func.count(Ticket.id).label("tickets_sold"),
        )
        .join(Order, Order.showtime_id == Showtime.id)
        .join(Ticket, Ticket.order_id == Order.id)
        .where(
            Order.status == "PAID",
            Showtime.starts_at >= now,
        )
        .group_by(Showtime.movie_id)
        .subquery()
    )

    recommendations_stmt = (
        select(
            Movie.id.label("movie_id"),
            Movie.title,
            Movie.description,
            Movie.runtime_minutes,
            Movie.rating,
            Movie.release_date,
            Movie.poster_url,
            upcoming_showtimes_subquery.c.next_showtime_starts_at,
            func.coalesce(trending_sales_subquery.c.tickets_sold, 0).label("tickets_sold"),
            Movie.metadata_json.label("metadata_json"),
        )
        .join(upcoming_showtimes_subquery, upcoming_showtimes_subquery.c.movie_id == Movie.id)
        .outerjoin(trending_sales_subquery, trending_sales_subquery.c.movie_id == Movie.id)
    )
    if watched_movie_ids:
        recommendations_stmt = recommendations_stmt.where(~Movie.id.in_(watched_movie_ids))

    recommendation_rows = (await session.execute(recommendations_stmt)).mappings().all()

    ranked_items = []
    for row in recommendation_rows:
        genres = _extract_genres(row["metadata_json"])
        genre_score = sum(genre_weights.get(genre.lower(), 0.0) for genre in genres)
        rating_score = rating_weights.get(str(row["rating"] or "").strip(), 0.0)
        tickets_sold = int(row["tickets_sold"] or 0)
        trend_score = min(tickets_sold, 100) / 10

        total_score = round((genre_score * 2.2) + (rating_score * 1.3) + trend_score, 3)

        if genre_score > 0 and genres:
            matching_genres = [
                genre for genre in genres if genre_weights.get(genre.lower(), 0.0) > 0
            ]
            if matching_genres:
                reason = f"Because you watch {matching_genres[0]} movies"
            else:
                reason = "Matched to your watch history"
        elif rating_score > 0:
            reason = f"Similar rating to your watched movies ({row['rating']})"
        elif tickets_sold > 0:
            reason = "Trending with other moviegoers"
        else:
            reason = "Upcoming pick"

        ranked_items.append(
            MovieRecommendationItem(
                movie_id=row["movie_id"],
                title=row["title"],
                description=row["description"],
                runtime_minutes=row["runtime_minutes"],
                rating=row["rating"],
                release_date=row["release_date"],
                poster_url=row["poster_url"],
                next_showtime_starts_at=row["next_showtime_starts_at"],
                reason=reason,
                score=total_score,
            )
        )

    ranked_items.sort(
        key=lambda item: (-item.score, item.next_showtime_starts_at),
    )

    items = ranked_items[:limit]
    return MovieRecommendationResponse(items=items, total=len(items))
