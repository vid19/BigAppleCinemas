from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin_user
from app.core.cache import delete_cache_prefix
from app.db.session import get_db_session
from app.models.movie import Movie
from app.models.reservation import ShowtimeSeatStatus
from app.models.showtime import Auditorium, Showtime, Theater
from app.schemas.catalog import (
    MovieCreate,
    MovieDetail,
    MovieUpdate,
    ShowtimeCreate,
    ShowtimeRead,
    ShowtimeUpdate,
    TheaterCreate,
    TheaterRead,
    TheaterUpdate,
)
from app.services.seat_inventory import sync_showtime_seat_statuses

router = APIRouter(dependencies=[Depends(require_admin_user)])


async def _invalidate_catalog_cache() -> None:
    await delete_cache_prefix("catalog:movies:")
    await delete_cache_prefix("catalog:movie:")
    await delete_cache_prefix("catalog:theaters:")
    await delete_cache_prefix("catalog:showtimes:")


def _apply_updates(instance: object, updates: dict) -> None:
    for field, value in updates.items():
        setattr(instance, field, value)


async def _get_showtime_read(session: AsyncSession, showtime_id: int) -> ShowtimeRead:
    stmt = (
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
        .where(Showtime.id == showtime_id)
    )
    row = (await session.execute(stmt)).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Showtime not found")
    return ShowtimeRead.model_validate(row)


@router.post("/movies", response_model=MovieDetail, status_code=status.HTTP_201_CREATED)
async def create_movie(
    payload: MovieCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MovieDetail:
    movie = Movie(**payload.model_dump())
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    await _invalidate_catalog_cache()
    return MovieDetail.model_validate(movie)


@router.patch("/movies/{movie_id}", response_model=MovieDetail)
async def update_movie(
    movie_id: int,
    payload: MovieUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> MovieDetail:
    movie = (await session.execute(select(Movie).where(Movie.id == movie_id))).scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return MovieDetail.model_validate(movie)

    _apply_updates(movie, updates)
    await session.commit()
    await session.refresh(movie)
    await _invalidate_catalog_cache()
    return MovieDetail.model_validate(movie)


@router.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    movie = (await session.execute(select(Movie).where(Movie.id == movie_id))).scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    await session.delete(movie)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Movie is referenced by other records and cannot be deleted",
        ) from exc
    await _invalidate_catalog_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/theaters", response_model=TheaterRead, status_code=status.HTTP_201_CREATED)
async def create_theater(
    payload: TheaterCreate,
    session: AsyncSession = Depends(get_db_session),
) -> TheaterRead:
    theater = Theater(**payload.model_dump())
    session.add(theater)
    await session.commit()
    await session.refresh(theater)
    await _invalidate_catalog_cache()
    return TheaterRead.model_validate(theater)


@router.patch("/theaters/{theater_id}", response_model=TheaterRead)
async def update_theater(
    theater_id: int,
    payload: TheaterUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TheaterRead:
    theater = (
        await session.execute(select(Theater).where(Theater.id == theater_id))
    ).scalar_one_or_none()
    if theater is None:
        raise HTTPException(status_code=404, detail="Theater not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return TheaterRead.model_validate(theater)

    _apply_updates(theater, updates)
    await session.commit()
    await session.refresh(theater)
    await _invalidate_catalog_cache()
    return TheaterRead.model_validate(theater)


@router.delete("/theaters/{theater_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theater(
    theater_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    theater = (
        await session.execute(select(Theater).where(Theater.id == theater_id))
    ).scalar_one_or_none()
    if theater is None:
        raise HTTPException(status_code=404, detail="Theater not found")

    await session.delete(theater)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Theater is referenced by other records and cannot be deleted",
        ) from exc
    await _invalidate_catalog_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/showtimes", response_model=ShowtimeRead, status_code=status.HTTP_201_CREATED)
async def create_showtime(
    payload: ShowtimeCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ShowtimeRead:
    if payload.starts_at >= payload.ends_at:
        raise HTTPException(status_code=400, detail="starts_at must be earlier than ends_at")

    movie_exists = (
        await session.execute(select(Movie.id).where(Movie.id == payload.movie_id))
    ).scalar_one_or_none()
    if movie_exists is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    auditorium_exists = (
        await session.execute(select(Auditorium.id).where(Auditorium.id == payload.auditorium_id))
    ).scalar_one_or_none()
    if auditorium_exists is None:
        raise HTTPException(status_code=404, detail="Auditorium not found")

    showtime = Showtime(**payload.model_dump())
    session.add(showtime)
    await session.flush()
    await sync_showtime_seat_statuses(session, showtime)
    await session.commit()
    await _invalidate_catalog_cache()
    return await _get_showtime_read(session, showtime.id)


@router.patch("/showtimes/{showtime_id}", response_model=ShowtimeRead)
async def update_showtime(
    showtime_id: int,
    payload: ShowtimeUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ShowtimeRead:
    showtime = (
        await session.execute(select(Showtime).where(Showtime.id == showtime_id))
    ).scalar_one_or_none()
    if showtime is None:
        raise HTTPException(status_code=404, detail="Showtime not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return await _get_showtime_read(session, showtime.id)

    if "starts_at" in updates or "ends_at" in updates:
        starts_at = updates.get("starts_at", showtime.starts_at)
        ends_at = updates.get("ends_at", showtime.ends_at)
        if starts_at >= ends_at:
            raise HTTPException(status_code=400, detail="starts_at must be earlier than ends_at")

    if "movie_id" in updates:
        movie_exists = (
            await session.execute(select(Movie.id).where(Movie.id == updates["movie_id"]))
        ).scalar_one_or_none()
        if movie_exists is None:
            raise HTTPException(status_code=404, detail="Movie not found")

    if "auditorium_id" in updates:
        auditorium_exists = (
            await session.execute(
                select(Auditorium.id).where(Auditorium.id == updates["auditorium_id"])
            )
        ).scalar_one_or_none()
        if auditorium_exists is None:
            raise HTTPException(status_code=404, detail="Auditorium not found")

    _apply_updates(showtime, updates)
    await session.flush()
    await sync_showtime_seat_statuses(session, showtime)
    await session.commit()
    await _invalidate_catalog_cache()
    return await _get_showtime_read(session, showtime.id)


@router.delete("/showtimes/{showtime_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_showtime(
    showtime_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    showtime = (
        await session.execute(select(Showtime).where(Showtime.id == showtime_id))
    ).scalar_one_or_none()
    if showtime is None:
        raise HTTPException(status_code=404, detail="Showtime not found")

    await session.execute(
        delete(ShowtimeSeatStatus).where(ShowtimeSeatStatus.showtime_id == showtime_id)
    )
    await session.delete(showtime)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Showtime is referenced by other records and cannot be deleted",
        ) from exc
    await _invalidate_catalog_cache()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
