import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.core.metrics import increment_metric
from app.core.rate_limit import create_rate_limiter
from app.db.session import get_db_session
from app.schemas.payment import (
    CheckoutDemoConfirmRequest,
    CheckoutFinalizeRead,
    CheckoutOrderStatusRead,
    CheckoutSessionCreate,
    CheckoutSessionRead,
    StripeWebhookAck,
    StripeWebhookEvent,
)
from app.services.payment_service import PaymentService

try:
    import stripe
except ModuleNotFoundError:  # pragma: no cover - resolved once dependency is installed
    stripe = None

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
    increment_metric("checkout_session_attempt_total")
    try:
        async with session.begin():
            checkout_session = await payment_service.create_checkout_session(
                session,
                user_id=user_id,
                reservation_id=payload.reservation_id,
                provider=payload.provider,
            )
    except HTTPException:
        increment_metric("checkout_session_failure_total")
        raise
    increment_metric("checkout_session_success_total")
    return checkout_session


@checkout_router.post("/demo/confirm", response_model=CheckoutFinalizeRead)
async def confirm_demo_checkout(
    payload: CheckoutDemoConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> CheckoutFinalizeRead:
    try:
        async with session.begin():
            order = await payment_service.get_order_for_user(
                session,
                order_id=payload.order_id,
                user_id=user_id,
            )
            finalized = await payment_service.finalize_paid_order(session, order=order)
    except HTTPException:
        increment_metric("checkout_finalize_failure_total")
        raise
    if finalized.order_status == "PAID":
        increment_metric("checkout_finalize_success_total")
    else:
        increment_metric("checkout_finalize_failure_total")
    return finalized


@checkout_router.get("/orders/{order_id}", response_model=CheckoutOrderStatusRead)
async def get_checkout_order_status(
    order_id: int,
    session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id),
) -> CheckoutOrderStatusRead:
    async with session.begin():
        return await payment_service.get_order_status_for_user(
            session,
            order_id=order_id,
            user_id=user_id,
        )


@webhook_router.post("/stripe", response_model=StripeWebhookAck)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    webhook_secret: str | None = Header(default=None, alias="x-webhook-secret"),
) -> StripeWebhookAck:
    raw_payload = await request.body()
    provider_session_id: str | None = None
    order_id: int | None = None

    if stripe_signature and settings.stripe_webhook_signing_secret:
        if stripe is None:
            raise HTTPException(status_code=503, detail="Stripe SDK not installed")
        try:
            stripe_event = stripe.Webhook.construct_event(
                payload=raw_payload,
                sig_header=stripe_signature,
                secret=settings.stripe_webhook_signing_secret,
            )
        except (stripe.error.SignatureVerificationError, ValueError) as exc:
            raise HTTPException(status_code=401, detail="Invalid Stripe signature") from exc

        event_id = str(stripe_event.get("id"))
        event_type = str(stripe_event.get("type"))
        object_payload = stripe_event.get("data", {}).get("object", {})
        provider_session_id = object_payload.get("id")
        metadata = object_payload.get("metadata") or {}
        raw_order_id = metadata.get("order_id") or object_payload.get("client_reference_id")
        if raw_order_id is not None:
            try:
                order_id = int(raw_order_id)
            except (TypeError, ValueError):
                order_id = None
    else:
        if webhook_secret != settings.stripe_webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
        try:
            payload = StripeWebhookEvent.model_validate(json.loads(raw_payload.decode("utf-8")))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc
        event_id = payload.event_id
        event_type = payload.type
        provider_session_id = payload.data.provider_session_id
        order_id = payload.data.order_id

    client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        key = f"webhook:stripe:event:{event_id}"
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

    if event_type != "checkout.session.completed":
        return StripeWebhookAck(acknowledged=True, duplicate=False, finalized=False)

    async with session.begin():
        if provider_session_id:
            order = await payment_service.get_order_by_provider_session(
                session,
                provider_session_id=provider_session_id,
            )
        elif order_id:
            order = await payment_service.get_order_by_id(
                session,
                order_id=order_id,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Webhook data must include provider_session_id or order_id",
            )

        finalized = await payment_service.finalize_paid_order(session, order=order)
        if finalized.order_status == "PAID":
            increment_metric("checkout_finalize_success_total")
        else:
            increment_metric("checkout_finalize_failure_total")
        return StripeWebhookAck(
            acknowledged=True,
            duplicate=False,
            finalized=True,
            order_status=finalized.order_status,
        )
