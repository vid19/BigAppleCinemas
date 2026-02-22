from datetime import datetime

from pydantic import BaseModel, Field


class CheckoutSessionCreate(BaseModel):
    reservation_id: int = Field(ge=1)
    provider: str = Field(default="MOCK_STRIPE", min_length=1, max_length=30)


class CheckoutSessionRead(BaseModel):
    order_id: int
    reservation_id: int
    provider: str
    provider_session_id: str
    status: str
    total_cents: int
    currency: str
    checkout_url: str
    created_at: datetime


class CheckoutDemoConfirmRequest(BaseModel):
    order_id: int = Field(ge=1)


class TicketRead(BaseModel):
    id: int
    seat_id: int
    qr_token: str
    status: str


class CheckoutFinalizeRead(BaseModel):
    order_id: int
    order_status: str
    ticket_count: int
    tickets: list[TicketRead]


class StripeWebhookData(BaseModel):
    provider_session_id: str | None = None
    order_id: int | None = Field(default=None, ge=1)


class StripeWebhookEvent(BaseModel):
    event_id: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=120)
    data: StripeWebhookData


class StripeWebhookAck(BaseModel):
    acknowledged: bool
    duplicate: bool = False
    finalized: bool = False
    order_status: str | None = None
