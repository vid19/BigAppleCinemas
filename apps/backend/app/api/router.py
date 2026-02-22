from fastapi import APIRouter

from app.api.v1 import (
    admin_catalog,
    admin_reports,
    auth,
    checkout,
    me,
    movies,
    reservations,
    showtimes,
    theaters,
    tickets,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
api_router.include_router(theaters.router, prefix="/theaters", tags=["theaters"])
api_router.include_router(showtimes.router, prefix="/showtimes", tags=["showtimes"])
api_router.include_router(admin_catalog.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_reports.router, prefix="/admin/reports", tags=["admin"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(checkout.checkout_router, prefix="/checkout", tags=["checkout"])
api_router.include_router(checkout.webhook_router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
