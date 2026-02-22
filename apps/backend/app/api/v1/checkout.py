from fastapi import APIRouter, Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.reservations import get_current_user_id
from app.core.config import settings
from app.core.rate_limit import create_rate_limiter
from app.db.session import get_db_session
from app.schemas.payment import (
    CheckoutDemoConfirmRequest,
    CheckoutFinalizeRead,
    CheckoutSessionCreate,
    CheckoutSessionRead,
    StripeWebhookAck,
    StripeWebhookEvent,
)
from app.services.payment_service import PaymentService

checkout_router = APIRouter()
webhook_router = APIRouter()
payment_service = PaymentService()
checkout_session_rate_limiter = create_rate_limiter(
    key_prefix="checkout:session",
    max_requests=lambda: settings.rate_limit_checkout_session,
    window_seconds=lambda: settings.rate_limit_checkout_window_seconds,
)


@checkout_router.post(
    "/session",
    response_model=CheckoutSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkout_session(
    payload: CheckoutSessionCreate,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(checkout_session_rate_limiter),
    user_id: int = Depends(get_current_user_id),
) -> CheckoutSessionRead:
    async with session.begin():
        return await payment_service.create_checkout_session(
            session,
            user_id=user_id,
            reservation_id=payload.reservation_id,
            provider=payload.provider,
        )


@checkout_router.post("/demo/confirm", response_model=CheckoutFinalizeRead)
async def confirm_demo_checkout(
    payload: CheckoutDemoConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> CheckoutFinalizeRead:
    async with session.begin():
        order = await payment_service.get_order_for_user(
            session,
            order_id=payload.order_id,
            user_id=user_id,
        )
        return await payment_service.finalize_paid_order(session, order=order)


@webhook_router.post("/stripe", response_model=StripeWebhookAck)
async def stripe_webhook(
    payload: StripeWebhookEvent,
    session: AsyncSession = Depends(get_db_session),
    webhook_secret: str | None = Header(default=None, alias="x-webhook-secret"),
) -> StripeWebhookAck:
    if webhook_secret != settings.stripe_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        key = f"webhook:stripe:event:{payload.event_id}"
        is_new_event = await client.set(
            key,
            "1",
            ex=settings.webhook_idempotency_ttl_seconds,
            nx=True,
        )
    finally:
        await client.aclose()

    if not is_new_event:
        return StripeWebhookAck(acknowledged=True, duplicate=True, finalized=False)

    if payload.type != "checkout.session.completed":
        return StripeWebhookAck(acknowledged=True, duplicate=False, finalized=False)

    async with session.begin():
        if payload.data.provider_session_id:
            order = await payment_service.get_order_by_provider_session(
                session,
                provider_session_id=payload.data.provider_session_id,
            )
        elif payload.data.order_id:
            order = await payment_service.get_order_by_id(
                session,
                order_id=payload.data.order_id,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Webhook data must include provider_session_id or order_id",
            )

        finalized = await payment_service.finalize_paid_order(session, order=order)
        return StripeWebhookAck(
            acknowledged=True,
            duplicate=False,
            finalized=True,
            order_status=finalized.order_status,
        )
