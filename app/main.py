from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.response import APIResponse
from app.api.v1.router import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")

    # TODO: Initialize infrastructure connections
    # - Database connection pool
    # - Redis connection
    # - Firebase Admin SDK

    # TODO: Initialize domain services
    # - Auth service
    # - Task service
    # - Device service
    # - Notification service

    print("Application startup complete")

    yield

    # Shutdown
    print("Shutting down application...")

    # TODO: Close infrastructure connections
    # - Close database connections
    # - Close Redis connections
    # - Close HTTP clients

    print("Application shutdown complete")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Backend API for Echo Executor Android App",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle application exceptions."""
        response = APIResponse.fail(
            code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        if settings.DEBUG:
            message = str(exc)
        else:
            message = "An unexpected error occurred"

        response = APIResponse.fail(
            code="INTERNAL_ERROR",
            message=message,
        )
        return JSONResponse(
            status_code=500,
            content=response.model_dump(mode="json"),
        )

    # Include routers
    app.include_router(api_v1_router)

    return app


app = create_app()
