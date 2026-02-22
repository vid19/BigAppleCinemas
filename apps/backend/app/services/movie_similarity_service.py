from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import delete_cache_prefix
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.movie import Movie
from app.models.order import Order, Ticket
from app.models.recommendation import MovieSimilarity
from app.models.showtime import Showtime


@dataclass
class _MovieFeatures:
    movie_id: int
    rating: str
    runtime_minutes: int
    genres: set[str]


def _extract_genres(metadata_json: dict | None) -> set[str]:
    if not isinstance(metadata_json, dict):
        return set()
    raw_genres = metadata_json.get("genre")
    if not isinstance(raw_genres, list):
        return set()
    return {str(genre).strip().lower() for genre in raw_genres if str(genre).strip()}


def _rating_similarity(left_rating: str, right_rating: str) -> float:
    if not left_rating or not right_rating:
        return 0.0
    if left_rating == right_rating:
        return 1.0
    left_prefix = left_rating[:2]
    right_prefix = right_rating[:2]
    if left_prefix == right_prefix:
        return 0.7
    return 0.35


def _runtime_similarity(left_runtime: int, right_runtime: int) -> float:
    distance = abs(left_runtime - right_runtime)
    return max(0.0, 1.0 - (distance / 140))


def _genre_similarity(left_genres: set[str], right_genres: set[str]) -> tuple[float, int]:
    if not left_genres or not right_genres:
        return 0.0, 0
    intersection = left_genres.intersection(right_genres)
    union = left_genres.union(right_genres)
    if not union:
        return 0.0, 0
    return len(intersection) / len(union), len(intersection)


async def rebuild_movie_similarity(
    session: AsyncSession,
    *,
    top_k: int | None = None,
) -> int:
    effective_top_k = (
        max(1, int(top_k))
        if top_k is not None
        else max(1, int(settings.recommendation_similarity_top_k))
    )
    movie_rows = (
        await session.execute(
            select(
                Movie.id,
                Movie.rating,
                Movie.runtime_minutes,
                Movie.metadata_json,
            )
        )
    ).all()
    features_by_movie: dict[int, _MovieFeatures] = {
        row.id: _MovieFeatures(
            movie_id=row.id,
            rating=row.rating or "",
            runtime_minutes=max(1, int(row.runtime_minutes or 1)),
            genres=_extract_genres(row.metadata_json),
        )
        for row in movie_rows
    }
    movie_ids = sorted(features_by_movie.keys())
    if len(movie_ids) < 2:
        await session.execute(delete(MovieSimilarity))
        await delete_cache_prefix("recommendations:")
        return 0

    watch_rows = (
        await session.execute(
            select(Order.user_id, Showtime.movie_id)
            .join(Showtime, Showtime.id == Order.showtime_id)
            .join(Ticket, Ticket.order_id == Order.id)
            .where(Order.status == "PAID")
            .distinct()
        )
    ).all()
    user_movies: defaultdict[int, set[int]] = defaultdict(set)
    for row in watch_rows:
        user_movies[int(row.user_id)].add(int(row.movie_id))

    co_watch_count: defaultdict[tuple[int, int], int] = defaultdict(int)
    for watched_movie_ids in user_movies.values():
        watched_list = sorted(watched_movie_ids)
        for index, left_movie_id in enumerate(watched_list):
            for right_movie_id in watched_list[index + 1 :]:
                co_watch_count[(left_movie_id, right_movie_id)] += 1
                co_watch_count[(right_movie_id, left_movie_id)] += 1

    similarity_rows: list[MovieSimilarity] = []
    max_co_watch = max(co_watch_count.values(), default=1)
    for movie_id in movie_ids:
        base = features_by_movie[movie_id]
        candidates: list[tuple[float, int, int, int]] = []
        for other_movie_id in movie_ids:
            if other_movie_id == movie_id:
                continue
            candidate = features_by_movie[other_movie_id]
            genre_similarity, shared_genre_count = _genre_similarity(base.genres, candidate.genres)
            rating_similarity = _rating_similarity(base.rating, candidate.rating)
            runtime_similarity = _runtime_similarity(
                base.runtime_minutes,
                candidate.runtime_minutes,
            )
            pair_co_watch = co_watch_count.get((movie_id, other_movie_id), 0)
            co_watch_similarity = pair_co_watch / max_co_watch
            score = (
                genre_similarity * 0.45
                + rating_similarity * 0.15
                + runtime_similarity * 0.15
                + co_watch_similarity * 0.25
            )
            candidates.append(
                (
                    round(score, 6),
                    other_movie_id,
                    pair_co_watch,
                    shared_genre_count,
                )
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        for score, similar_movie_id, pair_co_watch, shared_genre_count in candidates[
            :effective_top_k
        ]:
            similarity_rows.append(
                MovieSimilarity(
                    movie_id=movie_id,
                    similar_movie_id=similar_movie_id,
                    score=score,
                    co_watch_count=pair_co_watch,
                    shared_genre_count=shared_genre_count,
                    runtime_distance=abs(
                        base.runtime_minutes - features_by_movie[similar_movie_id].runtime_minutes
                    ),
                )
            )

    await session.execute(delete(MovieSimilarity))
    session.add_all(similarity_rows)
    await session.flush()
    await delete_cache_prefix("recommendations:")
    return len(similarity_rows)


async def rebuild_movie_similarity_job() -> int:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            return await rebuild_movie_similarity(session)
