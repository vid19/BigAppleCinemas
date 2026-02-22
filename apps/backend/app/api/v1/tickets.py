from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthenticatedUser, require_admin_user
from app.core.config import settings
from app.core.rate_limit import create_rate_limiter
from app.db.session import get_db_session
from app.models.order import Order, Ticket
from app.models.showtime import Seat
from app.schemas.portal import TicketScanRequest, TicketScanResponse

router = APIRouter()
ticket_scan_rate_limiter = create_rate_limiter(
    key_prefix="tickets:scan",
    max_requests=lambda: settings.rate_limit_ticket_scan,
    window_seconds=lambda: settings.rate_limit_ticket_scan_window_seconds,
)


@router.post("/scan", response_model=TicketScanResponse)
async def scan_ticket(
    payload: TicketScanRequest,
    session: AsyncSession = Depends(get_db_session),
    _: None = Depends(ticket_scan_rate_limiter),
    __: AuthenticatedUser = Depends(require_admin_user),
    staff_token: str | None = Header(default=None, alias="x-staff-token"),
) -> TicketScanResponse:
    if staff_token != settings.staff_scan_token:
        raise HTTPException(status_code=401, detail="Invalid staff scan token")

    async with session.begin():
        row = (
            await session.execute(
                select(Ticket, Order.showtime_id, Seat.seat_code)
                .join(Order, Order.id == Ticket.order_id)
                .join(Seat, Seat.id == Ticket.seat_id)
                .where(Ticket.qr_token == payload.qr_token)
                .with_for_update()
            )
        ).first()

        if row is None:
            return TicketScanResponse(
                result="INVALID",
                message="Ticket not found",
            )

        ticket, showtime_id, seat_code = row
        if ticket.status == "USED":
            return TicketScanResponse(
                result="ALREADY_USED",
                ticket_id=ticket.id,
                order_id=ticket.order_id,
                showtime_id=showtime_id,
                seat_code=seat_code,
                used_at=ticket.used_at,
                message="Ticket has already been used",
            )
        if ticket.status != "VALID":
            return TicketScanResponse(
                result="INVALID",
                ticket_id=ticket.id,
                order_id=ticket.order_id,
                showtime_id=showtime_id,
                seat_code=seat_code,
                used_at=ticket.used_at,
                message=f"Ticket is not valid for entry ({ticket.status})",
            )

        ticket.status = "USED"
        ticket.used_at = datetime.now(tz=UTC)
        await session.flush()
        return TicketScanResponse(
            result="VALID",
            ticket_id=ticket.id,
            order_id=ticket.order_id,
            showtime_id=showtime_id,
            seat_code=seat_code,
            used_at=ticket.used_at,
            message="Ticket validated and marked as used",
        )
