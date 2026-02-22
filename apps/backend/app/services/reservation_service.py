"""Reservation service scaffold.

Real lock-safe hold logic will be implemented in the reservation milestone:
- lock showtime seat rows with SELECT ... FOR UPDATE
- verify availability
- create reservation + reservation seats
- transition seat status AVAILABLE -> HELD
"""


class ReservationService:
    async def create_hold(self) -> None:
        raise NotImplementedError("Implemented in concurrency milestone")
