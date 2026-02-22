from datetime import datetime

from pydantic import BaseModel


class ReservationCreate(BaseModel):
    showtime_id: int
    seat_ids: list[int]


class ReservationRead(BaseModel):
    id: int
    showtime_id: int
    status: str
    expires_at: datetime
