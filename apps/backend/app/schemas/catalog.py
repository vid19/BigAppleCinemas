from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


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


class AuditoriumRead(BaseModel):
    id: int
    theater_id: int
    theater_name: str
    name: str
    seatmap_id: int | None


class AuditoriumListResponse(BaseModel):
    items: list[AuditoriumRead]
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


class ShowtimeSeatRead(BaseModel):
    seat_id: int
    seat_code: str
    row_label: str
    seat_number: int
    seat_type: str
    status: str


class ShowtimeSeatMapResponse(BaseModel):
    showtime_id: int
    movie_id: int
    auditorium_id: int
    theater_id: int
    theater_name: str
    starts_at: datetime
    seatmap_name: str | None
    layout_json: dict
    seats: list[ShowtimeSeatRead]


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    runtime_minutes: int = Field(ge=1, le=400)
    rating: str = Field(default="NR", min_length=1, max_length=10)
    release_date: date | None = None
    poster_url: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class MovieUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    runtime_minutes: int | None = Field(default=None, ge=1, le=400)
    rating: str | None = Field(default=None, min_length=1, max_length=10)
    release_date: date | None = None
    poster_url: str | None = None
    metadata_json: dict | None = None


class TheaterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=100)
    timezone: str = Field(min_length=1, max_length=50)


class TheaterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1, max_length=500)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=50)


class AuditoriumCreate(BaseModel):
    theater_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=100)
    seatmap_id: int | None = Field(default=None, ge=1)


class ShowtimeCreate(BaseModel):
    movie_id: int = Field(ge=1)
    auditorium_id: int = Field(ge=1)
    starts_at: datetime
    ends_at: datetime
    status: str = Field(default="SCHEDULED", min_length=1, max_length=30)


class ShowtimeUpdate(BaseModel):
    movie_id: int | None = Field(default=None, ge=1)
    auditorium_id: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = Field(default=None, min_length=1, max_length=30)
