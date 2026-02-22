from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from math import log1p

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.cache import delete_cache_prefix, get_cache_json, set_cache_json
from app.core.config import settings
from app.core.metrics import increment_metric
from app.db.session import get_db_session
from app.models.movie import Movie
from app.models.order import Order, Ticket
from app.models.recommendation import MovieSimilarity, UserMovieEvent
from app.models.showtime import Auditorium, Seat, Showtime, Theater
from app.schemas.portal import (
    MovieRecommendationItem,
    MovieRecommendationResponse,
    MyOrderItem,
    MyOrderListResponse,
    MyTicketItem,
    MyTicketListResponse,
    RecommendationFeedbackRead,
    RecommendationFeedbackWrite,
)

router = APIRouter()
NOT_INTERESTED = "NOT_INTERESTED"
SAVE_FOR_LATER = "SAVE_FOR_LATER"


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


def _freshness_score(
    *,
    now: datetime,
    next_showtime_starts_at: datetime,
    release_date: date | None,
) -> float:
    hours_until_showtime = max(
        (next_showtime_starts_at - now).total_seconds() / 3600,
        0.0,
    )
    showtime_freshness = max(0.0, 1.0 - min(hours_until_showtime / 96.0, 1.0))

    release_freshness = 0.0
    if release_date is not None:
        age_days = (now.date() - release_date).days
        if age_days <= 0:
            release_freshness = 1.0
        else:
            release_freshness = max(0.0, 1.0 - min(age_days / 140.0, 1.0))

    return (showtime_freshness * 0.65) + (release_freshness * 0.35)


def _weights_for_variant(variant: str) -> tuple[float, float, float]:
    if variant.upper() == "B":
        return (0.48, 0.32, 0.20)
    return (0.60, 0.22, 0.18)


def _recommendation_reason(
    *,
    source_movie_id: int | None,
    watched_titles: dict[int, str],
    genres: list[str],
    genre_weights: dict[str, float],
    tickets_sold: int,
    is_saved_for_later: bool,
) -> str:
    if is_saved_for_later:
        return "Saved for later"

    if source_movie_id is not None and source_movie_id in watched_titles:
        return f"Because you watched {watched_titles[source_movie_id]}"

    if genres:
        matching_genres = [genre for genre in genres if genre_weights.get(genre.lower(), 0.0) > 0]
        if matching_genres:
            return f"Because you watch {matching_genres[0]} movies"

    if tickets_sold > 0:
        return "Trending with other moviegoers"

    return "Fresh pick for tonight"


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


@router.post(
    "/recommendations/feedback",
    response_model=RecommendationFeedbackRead,
    status_code=status.HTTP_200_OK,
)
async def submit_recommendation_feedback(
    payload: RecommendationFeedbackWrite,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> RecommendationFeedbackRead:
    now = datetime.now(tz=UTC)
    async with session.begin():
        movie_exists = (
            await session.execute(select(Movie.id).where(Movie.id == payload.movie_id))
        ).scalar_one_or_none()
        if movie_exists is None:
            raise HTTPException(status_code=404, detail="Movie not found")

        await session.execute(
            delete(UserMovieEvent).where(
                UserMovieEvent.user_id == user_id,
                UserMovieEvent.movie_id == payload.movie_id,
                UserMovieEvent.event_type != payload.event_type,
                UserMovieEvent.event_type.in_([NOT_INTERESTED, SAVE_FOR_LATER]),
            )
        )
        existing_event = (
            await session.execute(
                select(UserMovieEvent)
                .where(
                    UserMovieEvent.user_id == user_id,
                    UserMovieEvent.movie_id == payload.movie_id,
                    UserMovieEvent.event_type == payload.event_type,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()

        recorded_at: datetime | None = None
        if payload.active:
            if existing_event is None:
                existing_event = UserMovieEvent(
                    user_id=user_id,
                    movie_id=payload.movie_id,
                    event_type=payload.event_type,
                )
                session.add(existing_event)
                await session.flush()
            recorded_at = existing_event.created_at if existing_event.created_at else now
        else:
            if existing_event is not None:
                await session.delete(existing_event)

    await delete_cache_prefix(f"recommendations:{user_id}:")
    increment_metric("recommendation_feedback_total")
    return RecommendationFeedbackRead(
        movie_id=payload.movie_id,
        event_type=payload.event_type,
        active=payload.active,
        recorded_at=recorded_at,
    )


@router.get("/recommendations", response_model=MovieRecommendationResponse)
async def list_my_recommendations(
    limit: int = Query(default=8, ge=1, le=20),
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> MovieRecommendationResponse:
    variant = settings.recommendation_ranker_variant.upper()
    cache_key = f"recommendations:{user_id}:{variant}:{limit}"
    cached_payload = await get_cache_json(cache_key)
    if cached_payload is not None:
        return MovieRecommendationResponse.model_validate(cached_payload)

    now = datetime.now(tz=UTC)
    feedback_rows = (
        await session.execute(
            select(UserMovieEvent.movie_id, UserMovieEvent.event_type).where(
                UserMovieEvent.user_id == user_id,
                UserMovieEvent.event_type.in_([NOT_INTERESTED, SAVE_FOR_LATER]),
            )
        )
    ).all()
    not_interested_movie_ids = {
        int(movie_id)
        for movie_id, event_type in feedback_rows
        if event_type == NOT_INTERESTED
    }
    saved_for_later_movie_ids = {
        int(movie_id)
        for movie_id, event_type in feedback_rows
        if event_type == SAVE_FOR_LATER
    }

    watch_history_stmt = (
        select(
            Movie.id.label("movie_id"),
            Movie.title.label("movie_title"),
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
    watched_titles = {
        int(row["movie_id"]): str(row["movie_title"])
        for row in watch_history_rows
        if row["movie_title"]
    }
    watch_count_by_movie = {
        int(row["movie_id"]): float(row["watch_count"] or 1)
        for row in watch_history_rows
    }
    genre_weights: defaultdict[str, float] = defaultdict(float)
    rating_weights: defaultdict[str, float] = defaultdict(float)
    for row in watch_history_rows:
        weight = float(row["watch_count"] or 1)
        rating = str(row["rating"] or "").strip()
        if rating:
            rating_weights[rating] += weight
        for genre in _extract_genres(row["metadata_json"]):
            genre_weights[genre.lower()] += weight

    similarity_score_by_movie: defaultdict[int, float] = defaultdict(float)
    top_source_by_movie: dict[int, tuple[float, int]] = {}
    if watched_movie_ids:
        similarity_stmt = select(
            MovieSimilarity.movie_id.label("source_movie_id"),
            MovieSimilarity.similar_movie_id.label("candidate_movie_id"),
            MovieSimilarity.score.label("score"),
        ).where(MovieSimilarity.movie_id.in_(watched_movie_ids))
        similarity_rows = (await session.execute(similarity_stmt)).mappings().all()
        for row in similarity_rows:
            source_movie_id = int(row["source_movie_id"])
            candidate_movie_id = int(row["candidate_movie_id"])
            watch_weight = watch_count_by_movie.get(source_movie_id, 1.0)
            contribution = float(row["score"] or 0.0) * (1.0 + log1p(watch_weight))
            if contribution <= 0:
                continue
            similarity_score_by_movie[candidate_movie_id] += contribution
            top_source = top_source_by_movie.get(candidate_movie_id)
            if top_source is None or contribution > top_source[0]:
                top_source_by_movie[candidate_movie_id] = (contribution, source_movie_id)

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
    if not_interested_movie_ids:
        recommendations_stmt = recommendations_stmt.where(~Movie.id.in_(not_interested_movie_ids))

    recommendation_rows = (await session.execute(recommendations_stmt)).mappings().all()
    max_similarity = max(similarity_score_by_movie.values(), default=0.0)
    max_popularity = max(
        (log1p(int(row["tickets_sold"] or 0)) for row in recommendation_rows),
        default=0.0,
    )
    personalized_weight, popularity_weight, freshness_weight = _weights_for_variant(variant)
    candidate_rows = []
    for row in recommendation_rows:
        movie_id = int(row["movie_id"])
        genres = _extract_genres(row["metadata_json"])
        primary_genre = genres[0].lower() if genres else None
        tickets_sold = int(row["tickets_sold"] or 0)
        similarity_raw = similarity_score_by_movie.get(movie_id, 0.0)
        similarity_score = similarity_raw / max_similarity if max_similarity > 0 else 0.0
        popularity_raw = log1p(tickets_sold)
        popularity_score = popularity_raw / max_popularity if max_popularity > 0 else 0.0
        freshness_score = _freshness_score(
            now=now,
            next_showtime_starts_at=row["next_showtime_starts_at"],
            release_date=row["release_date"],
        )
        rating_score = rating_weights.get(str(row["rating"] or "").strip(), 0.0)
        rating_bonus = min(rating_score / 4.0, 0.10) if rating_score > 0 else 0.0
        save_for_later_bonus = (
            settings.recommendation_save_for_later_boost
            if movie_id in saved_for_later_movie_ids
            else 0.0
        )
        base_score = (
            (similarity_score * personalized_weight)
            + (popularity_score * popularity_weight)
            + (freshness_score * freshness_weight)
            + rating_bonus
            + save_for_later_bonus
        )
        source_data = top_source_by_movie.get(movie_id)
        source_movie_id = source_data[1] if source_data else None
        candidate_rows.append(
            {
                "movie_id": movie_id,
                "title": row["title"],
                "description": row["description"],
                "runtime_minutes": row["runtime_minutes"],
                "rating": row["rating"],
                "release_date": row["release_date"],
                "poster_url": row["poster_url"],
                "next_showtime_starts_at": row["next_showtime_starts_at"],
                "tickets_sold": tickets_sold,
                "genres": genres,
                "primary_genre": primary_genre,
                "source_movie_id": source_movie_id,
                "base_score": base_score,
            }
        )

    candidate_rows.sort(key=lambda row: row["base_score"], reverse=True)
    remaining_rows = candidate_rows.copy()
    selected_rows = []
    selected_genre_counts: Counter[str] = Counter()

    while remaining_rows and len(selected_rows) < limit:
        best_index = 0
        best_adjusted_score = float("-inf")
        for index, row in enumerate(remaining_rows):
            genre_penalty = 0.0
            if row["primary_genre"]:
                genre_penalty = (
                    selected_genre_counts[row["primary_genre"]]
                    * settings.recommendation_diversity_penalty
                )
            adjusted_score = row["base_score"] - genre_penalty
            if adjusted_score > best_adjusted_score:
                best_adjusted_score = adjusted_score
                best_index = index

        selected = remaining_rows.pop(best_index)
        if selected["primary_genre"]:
            selected_genre_counts[selected["primary_genre"]] += 1
        selected["score"] = round(max(best_adjusted_score, 0.0) * 100, 3)
        selected_rows.append(selected)

    items = [
        MovieRecommendationItem(
            movie_id=row["movie_id"],
            title=row["title"],
            description=row["description"],
            runtime_minutes=row["runtime_minutes"],
            rating=row["rating"],
            release_date=row["release_date"],
            poster_url=row["poster_url"],
            next_showtime_starts_at=row["next_showtime_starts_at"],
            reason=_recommendation_reason(
                source_movie_id=row["source_movie_id"],
                watched_titles=watched_titles,
                genres=row["genres"],
                genre_weights=genre_weights,
                tickets_sold=row["tickets_sold"],
                is_saved_for_later=row["movie_id"] in saved_for_later_movie_ids,
            ),
            score=row["score"],
        )
        for row in selected_rows
    ]

    response = MovieRecommendationResponse(items=items, total=len(items))
    await set_cache_json(
        cache_key,
        response.model_dump(mode="json"),
        ttl_seconds=settings.recommendation_cache_ttl_seconds,
    )
    return response
