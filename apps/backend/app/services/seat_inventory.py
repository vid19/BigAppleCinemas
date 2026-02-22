from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import ShowtimeSeatStatus
from app.models.showtime import Auditorium, Seat, SeatMap, Showtime

DEFAULT_ROWS = tuple("ABCDEFGH")
DEFAULT_SEATS_PER_ROW = 12


def _default_layout_json() -> dict:
    return {
        "rows": list(DEFAULT_ROWS),
        "seats_per_row": DEFAULT_SEATS_PER_ROW,
        "aisles_after": [4, 8],
        "screen_position": "top",
    }


def _seat_type_for_row(row_label: str) -> str:
    if row_label in {"A", "B"}:
        return "VIP"
    if row_label in {"C", "D"}:
        return "PREMIUM"
    return "STANDARD"


async def ensure_auditorium_seat_inventory(
    session: AsyncSession,
    auditorium: Auditorium,
) -> None:
    if auditorium.seatmap_id is None:
        seatmap = SeatMap(
            name=f"{auditorium.name} Standard Layout",
            layout_json=_default_layout_json(),
        )
        session.add(seatmap)
        await session.flush()
        auditorium.seatmap_id = seatmap.id

    seat_count = (
        await session.execute(
            select(func.count(Seat.id)).where(Seat.auditorium_id == auditorium.id)
        )
    ).scalar_one()
    if seat_count > 0:
        return

    seats = []
    for row_label in DEFAULT_ROWS:
        for seat_number in range(1, DEFAULT_SEATS_PER_ROW + 1):
            seats.append(
                Seat(
                    auditorium_id=auditorium.id,
                    seat_code=f"{row_label}{seat_number}",
                    row_label=row_label,
                    seat_number=seat_number,
                    seat_type=_seat_type_for_row(row_label),
                )
            )
    session.add_all(seats)
    await session.flush()


async def sync_showtime_seat_statuses(
    session: AsyncSession,
    showtime: Showtime,
) -> None:
    seat_ids = list(
        (
            await session.execute(
                select(Seat.id).where(Seat.auditorium_id == showtime.auditorium_id)
            )
        ).scalars()
    )
    if not seat_ids:
        return

    existing_seat_ids = set(
        (
            await session.execute(
                select(ShowtimeSeatStatus.seat_id).where(
                    ShowtimeSeatStatus.showtime_id == showtime.id
                )
            )
        ).scalars()
    )
    target_seat_ids = set(seat_ids)

    stale_seat_ids = [seat_id for seat_id in existing_seat_ids if seat_id not in target_seat_ids]
    if stale_seat_ids:
        await session.execute(
            delete(ShowtimeSeatStatus).where(
                ShowtimeSeatStatus.showtime_id == showtime.id,
                ShowtimeSeatStatus.seat_id.in_(stale_seat_ids),
            )
        )

    missing_seat_ids = [seat_id for seat_id in seat_ids if seat_id not in existing_seat_ids]
    if not missing_seat_ids:
        return

    session.add_all(
        [
            ShowtimeSeatStatus(
                showtime_id=showtime.id,
                seat_id=seat_id,
                status="AVAILABLE",
                held_by_reservation_id=None,
            )
            for seat_id in missing_seat_ids
        ]
    )
