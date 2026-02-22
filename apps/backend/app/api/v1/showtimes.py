from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache_json, set_cache_json
from app.db.session import get_db_session
from app.models.reservation import ShowtimeSeatStatus
from app.models.showtime import Auditorium, Seat, SeatMap, Showtime, Theater
from app.schemas.catalog import (
    ShowtimeListResponse,
    ShowtimeRead,
    ShowtimeSeatMapResponse,
    ShowtimeSeatRead,
)

router = APIRouter()


@router.get("", response_model=ShowtimeListResponse)
async def list_showtimes(
    movie_id: int | None = Query(default=None),
    theater_id: int | None = Query(default=None),
    show_date: date | None = Query(default=None, alias="date"),
    include_past: bool = Query(default=False),
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ShowtimeListResponse:
    now_utc = datetime.now(tz=UTC)
    show_date_text = show_date.isoformat() if show_date else ""
    freshness_bucket = now_utc.strftime("%Y%m%d%H%M") if not include_past else "all"
    cache_key = (
        "catalog:showtimes:"
        f"movie_id={movie_id or ''}:"
        f"theater_id={theater_id or ''}:"
        f"date={show_date_text}:"
        f"include_past={include_past}:"
        f"freshness={freshness_bucket}:"
        f"limit={limit}:offset={offset}"
    )
    cached = await get_cache_json(cache_key)
    if cached is not None:
        return ShowtimeListResponse.model_validate(cached)

    filters = []
    if movie_id is not None:
        filters.append(Showtime.movie_id == movie_id)
    if theater_id is not None:
        filters.append(Theater.id == theater_id)
    if show_date is not None:
        filters.append(func.date(Showtime.starts_at) == show_date)
    if not include_past:
        filters.append(Showtime.starts_at >= now_utc)

    join_stmt = (
        select(
            Showtime.id,
            Showtime.movie_id,
            Showtime.auditorium_id,
            Theater.id.label("theater_id"),
            Theater.name.label("theater_name"),
            Showtime.starts_at,
            Showtime.ends_at,
            Showtime.status,
        )
        .join(Auditorium, Auditorium.id == Showtime.auditorium_id)
        .join(Theater, Theater.id == Auditorium.theater_id)
    )

    if filters:
        join_stmt = join_stmt.where(and_(*filters))

    total_stmt = (
        select(func.count(Showtime.id))
        .join(Auditorium, Auditorium.id == Showtime.auditorium_id)
        .join(Theater, Theater.id == Auditorium.theater_id)
    )
    if filters:
        total_stmt = total_stmt.where(and_(*filters))
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = join_stmt.order_by(Showtime.starts_at.asc()).offset(offset).limit(limit)
    rows = (await session.execute(stmt)).mappings().all()

    items = [ShowtimeRead.model_validate(row) for row in rows]
    response = ShowtimeListResponse(items=items, total=total, limit=limit, offset=offset)
    await set_cache_json(cache_key, response.model_dump(mode="json"))
    return response


@router.get("/{showtime_id}/seats", response_model=ShowtimeSeatMapResponse)
async def get_showtime_seats(
    showtime_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ShowtimeSeatMapResponse:
    showtime_stmt = (
        select(
            Showtime.id,
            Showtime.movie_id,
            Showtime.auditorium_id,
            Showtime.starts_at,
            Theater.id.label("theater_id"),
            Theater.name.label("theater_name"),
            SeatMap.name.label("seatmap_name"),
            SeatMap.layout_json.label("layout_json"),
        )
        .join(Auditorium, Auditorium.id == Showtime.auditorium_id)
        .join(Theater, Theater.id == Auditorium.theater_id)
        .outerjoin(SeatMap, SeatMap.id == Auditorium.seatmap_id)
        .where(Showtime.id == showtime_id)
    )
    showtime_row = (await session.execute(showtime_stmt)).mappings().first()
    if showtime_row is None:
        raise HTTPException(status_code=404, detail="Showtime not found")

    seat_stmt = (
        select(
            Seat.id.label("seat_id"),
            Seat.seat_code,
            Seat.row_label,
            Seat.seat_number,
            Seat.seat_type,
            func.coalesce(ShowtimeSeatStatus.status, "AVAILABLE").label("status"),
        )
        .outerjoin(
            ShowtimeSeatStatus,
            and_(
                ShowtimeSeatStatus.seat_id == Seat.id,
                ShowtimeSeatStatus.showtime_id == showtime_id,
            ),
        )
        .where(Seat.auditorium_id == showtime_row["auditorium_id"])
        .order_by(Seat.row_label.asc(), Seat.seat_number.asc())
    )
    seat_rows = (await session.execute(seat_stmt)).mappings().all()

    return ShowtimeSeatMapResponse(
        showtime_id=showtime_row["id"],
        movie_id=showtime_row["movie_id"],
        auditorium_id=showtime_row["auditorium_id"],
        theater_id=showtime_row["theater_id"],
        theater_name=showtime_row["theater_name"],
        starts_at=showtime_row["starts_at"],
        seatmap_name=showtime_row["seatmap_name"],
        layout_json=showtime_row["layout_json"] or {},
        seats=[ShowtimeSeatRead.model_validate(row) for row in seat_rows],
    )
