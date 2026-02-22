from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.movie import Movie
from app.schemas.catalog import MovieDetail, MovieListResponse

router = APIRouter()


@router.get("", response_model=MovieListResponse)
async def list_movies(
    q: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> MovieListResponse:
    filters = []
    if q:
        filters.append(Movie.title.ilike(f"%{q.strip()}%"))

    total_stmt = select(func.count(Movie.id))
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = (
        select(Movie)
        .where(*filters)
        .order_by(Movie.release_date.desc().nullslast(), Movie.title.asc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()

    return MovieListResponse(items=rows, total=total, limit=limit, offset=offset)


@router.get("/{movie_id}", response_model=MovieDetail)
async def get_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> MovieDetail:
    stmt = select(Movie).where(Movie.id == movie_id)
    movie = (await session.execute(stmt)).scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")

    return MovieDetail.model_validate(movie)
