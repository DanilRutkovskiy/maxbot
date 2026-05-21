import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.routes import health_router, tasks_router, webhook_router
from app.config.settings import get_settings
from app.schemas.api import ErrorResponse
from app.utils.exceptions import AppError
from app.utils.logging import setup_logging
from app.utils.request_context import generate_request_id, set_request_id


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    settings.ensure_directories()
    yield


app = FastAPI(
    title="MAX Portrait Animation Bot",
    version=__version__,
    lifespan=lifespan,
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIdMiddleware)
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(webhook_router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=exc.message,
            code=exc.code,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = generate_request_id()
    set_request_id(request_id)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="internal_error",
            detail={"trace": traceback.format_exc()[-500:]},
        ).model_dump(),
    )
