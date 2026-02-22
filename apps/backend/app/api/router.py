from fastapi import APIRouter

from app.api.v1 import auth, movies, reservations, tickets

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
