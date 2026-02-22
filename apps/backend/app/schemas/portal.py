from datetime import date, datetime

from pydantic import BaseModel, Field


class TicketScanRequest(BaseModel):
    qr_token: str = Field(min_length=1, max_length=255)


class TicketScanResponse(BaseModel):
    result: str
    ticket_id: int | None = None
    order_id: int | None = None
    showtime_id: int | None = None
    seat_code: str | None = None
    used_at: datetime | None = None
    message: str


class MyTicketItem(BaseModel):
    ticket_id: int
    order_id: int
    qr_token: str
    ticket_status: str
    seat_code: str
    seat_type: str
    movie_title: str
    theater_name: str
    showtime_id: int
    showtime_starts_at: datetime
    showtime_ends_at: datetime | None
    used_at: datetime | None
    created_at: datetime


class MyTicketListResponse(BaseModel):
    items: list[MyTicketItem]
    total: int


class MyOrderItem(BaseModel):
    order_id: int
    reservation_id: int
    showtime_id: int
    status: str
    total_cents: int
    currency: str
    provider: str
    ticket_count: int
    created_at: datetime


class MyOrderListResponse(BaseModel):
    items: list[MyOrderItem]
    total: int


class MovieRecommendationItem(BaseModel):
    movie_id: int
    title: str
    description: str
    runtime_minutes: int
    rating: str
    release_date: date | None
    poster_url: str | None
    next_showtime_starts_at: datetime
    reason: str
    score: float


class MovieRecommendationResponse(BaseModel):
    items: list[MovieRecommendationItem]
    total: int


class RecommendationFeedbackWrite(BaseModel):
    movie_id: int = Field(ge=1)
    event_type: str = Field(pattern="^(NOT_INTERESTED|SAVE_FOR_LATER)$")
    active: bool = True


class RecommendationFeedbackRead(BaseModel):
    movie_id: int
    event_type: str
    active: bool
    recorded_at: datetime | None = None


class RecommendationEventWrite(BaseModel):
    movie_id: int = Field(ge=1)
    event_type: str = Field(pattern="^(IMPRESSION|CLICK)$")


class RecommendationEventRead(BaseModel):
    movie_id: int
    event_type: str
    recorded: bool


class AdminShowtimeSalesItem(BaseModel):
    showtime_id: int
    movie_title: str
    theater_name: str
    starts_at: datetime
    sold_seats: int
    capacity: int
    occupancy_percent: float


class AdminSalesReportResponse(BaseModel):
    paid_orders: int
    gross_revenue_cents: int
    tickets_sold: int
    active_holds: int
    showtimes: list[AdminShowtimeSalesItem]
    recommendation_impressions: int = 0
    recommendation_clicks: int = 0
    recommendation_saved: int = 0
    recommendation_hidden: int = 0
    recommendation_ctr_percent: float = 0.0
    recommendation_save_rate_percent: float = 0.0
    recommendation_hide_rate_percent: float = 0.0
