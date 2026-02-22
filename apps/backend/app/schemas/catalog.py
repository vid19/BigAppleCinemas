from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MovieListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    runtime_minutes: int
    rating: str
    release_date: date | None
    poster_url: str | None


class MovieDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    runtime_minutes: int
    rating: str
    release_date: date | None
    poster_url: str | None
    metadata_json: dict


class MovieListResponse(BaseModel):
    items: list[MovieListItem]
    total: int
    limit: int
    offset: int


class TheaterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    city: str
    timezone: str


class TheaterListResponse(BaseModel):
    items: list[TheaterRead]
    total: int
    limit: int
    offset: int


class ShowtimeRead(BaseModel):
    id: int
    movie_id: int
    auditorium_id: int
    theater_id: int
    theater_name: str
    starts_at: datetime
    ends_at: datetime
    status: str


class ShowtimeListResponse(BaseModel):
    items: list[ShowtimeRead]
    total: int
    limit: int
    offset: int
