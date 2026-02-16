"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from app.config import settings
from app.database import engine, Base, async_session_factory
from app.models import *  # noqa: F401,F403 - Import all models for table creation
from app.models.user import User
from app.utils.password import hash_password

# Routers
from app.routers import auth, users, entries, overtime, absences, departments, holidays, schedule, reports, export, backup, timer, data

logger = logging.getLogger("timetracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting Time Tracker API...")

    # Create tables if they don't exist (for development; use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create default admin account if no users exist
    async with async_session_factory() as session:
        result = await session.execute(select(User).limit(1))
        if not result.scalar_one_or_none():
            admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                first_name="Admin",
                last_name="User",
                role="admin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info(f"Created default admin account: {settings.ADMIN_EMAIL}")

    # Ensure every user has at least one work schedule (backfill)
    async with async_session_factory() as session:
        from app.models.work_schedule import WorkSchedule
        from datetime import date as date_type
        from sqlalchemy import exists

        users_without_schedule = await session.execute(
            select(User).where(
                ~exists(
                    select(WorkSchedule.id).where(WorkSchedule.user_id == User.id)
                )
            )
        )
        count = 0
        for u in users_without_schedule.scalars().all():
            session.add(WorkSchedule(
                user_id=u.id,
                valid_from=date_type(2020, 1, 1),
                monday_minutes=480,
                tuesday_minutes=480,
                wednesday_minutes=480,
                thursday_minutes=480,
                friday_minutes=480,
                saturday_minutes=0,
                sunday_minutes=0,
            ))
            count += 1
        if count:
            await session.commit()
            logger.info(f"Created default work schedules for {count} users")

    logger.info("Time Tracker API started successfully.")
    yield

    # Shutdown
    logger.info("Shutting down Time Tracker API...")
    await engine.dispose()


# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create app
app = FastAPI(
    title="Time Tracker API",
    description="Full-stack time tracking application with overtime management",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(entries.router, prefix=API_PREFIX)
app.include_router(overtime.router, prefix=API_PREFIX)
app.include_router(absences.router, prefix=API_PREFIX)
app.include_router(departments.router, prefix=API_PREFIX)
app.include_router(holidays.router, prefix=API_PREFIX)
app.include_router(schedule.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)
app.include_router(export.router, prefix=API_PREFIX)
app.include_router(backup.router, prefix=API_PREFIX)
app.include_router(timer.router, prefix=API_PREFIX)
app.include_router(data.router, prefix=API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/v1")
async def api_root():
    """API root information."""
    return {
        "name": "Time Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
    }
