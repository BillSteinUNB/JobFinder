"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analytics, applications, jobs, resume
from api.state import AppState


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and cleanup application state."""
    # Initialize shared state
    app.state.app_state = AppState()
    yield
    # Cleanup
    if hasattr(app.state, "app_state"):
        app.state.app_state.cleanup()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Job Finder API",
        description="Backend API for Job Finder - connects resume to job recommendations",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative dev port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
    app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

    @app.get("/api/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}

    return app


app = create_app()
