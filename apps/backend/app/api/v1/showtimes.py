from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.showtime import Auditorium, Showtime, Theater
from app.schemas.catalog import ShowtimeListResponse, ShowtimeRead

router = APIRouter()


@router.get("", response_model=ShowtimeListResponse)
async def list_showtimes(
    movie_id: int | None = Query(default=None),
    theater_id: int | None = Query(default=None),
    show_date: date | None = Query(default=None, alias="date"),
    limit: int = Query(default=40, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ShowtimeListResponse:
    filters = []
    if movie_id is not None:
        filters.append(Showtime.movie_id == movie_id)
    if theater_id is not None:
        filters.append(Theater.id == theater_id)
    if show_date is not None:
        filters.append(func.date(Showtime.starts_at) == show_date)

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
    return ShowtimeListResponse(items=items, total=total, limit=limit, offset=offset)
