from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.showtime import Theater
from app.schemas.catalog import TheaterListResponse

router = APIRouter()


@router.get("", response_model=TheaterListResponse)
async def list_theaters(
    city: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> TheaterListResponse:
    filters = []
    if city:
        filters.append(Theater.city.ilike(f"%{city.strip()}%"))

    total_stmt = select(func.count(Theater.id))
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = (
        select(Theater)
        .where(*filters)
        .order_by(Theater.city.asc(), Theater.name.asc())
        .offset(offset)
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()

    return TheaterListResponse(items=rows, total=total, limit=limit, offset=offset)
