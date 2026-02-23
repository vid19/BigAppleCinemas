from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TicketLifecycleWindow:
    entry_opens_at: datetime
    active_until_at: datetime


def build_ticket_lifecycle_window(
    *,
    showtime_starts_at: datetime,
    showtime_ends_at: datetime | None,
    entry_open_minutes: int,
    active_grace_minutes: int,
) -> TicketLifecycleWindow:
    entry_opens_at = showtime_starts_at - timedelta(minutes=max(entry_open_minutes, 0))
    effective_end_at = showtime_ends_at or showtime_starts_at
    active_until_at = effective_end_at + timedelta(minutes=max(active_grace_minutes, 0))
    return TicketLifecycleWindow(
        entry_opens_at=entry_opens_at,
        active_until_at=active_until_at,
    )


def resolve_ticket_lifecycle_state(
    *,
    ticket_status: str,
    now: datetime,
    window: TicketLifecycleWindow,
) -> str:
    normalized_status = ticket_status.upper().strip()
    if normalized_status == "USED":
        return "USED"
    if normalized_status == "VOID":
        return "VOID"
    if normalized_status != "VALID":
        return "INVALID"
    if now < window.entry_opens_at:
        return "UPCOMING"
    if now <= window.active_until_at:
        return "ACTIVE"
    return "EXPIRED"
