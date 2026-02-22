import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.bootstrap import bootstrap_local_data

request_logger = logging.getLogger("app.request")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.environment == "local" and settings.bootstrap_demo_data:
        await bootstrap_local_data()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
allow_origins = [
    origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or uuid4().hex
    request.state.request_id = request_id
    started_at = perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    duration_ms = (perf_counter() - started_at) * 1000
    request_logger.info(
        "request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response

app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
