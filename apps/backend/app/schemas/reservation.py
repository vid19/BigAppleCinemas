from datetime import datetime

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    showtime_id: int = Field(ge=1)
    seat_ids: list[int] = Field(min_length=1)


class ReservationRead(BaseModel):
    id: int
    user_id: int
    showtime_id: int
    status: str
    expires_at: datetime
    seat_ids: list[int]
    created_at: datetime
