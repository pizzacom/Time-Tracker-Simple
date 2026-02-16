"""Shared fixtures for the test suite.

Uses SQLite via aiosqlite. Every test gets a fresh database
(all tables created before, dropped after).
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID as pgUUID

# ── Make PostgreSQL UUID type work on SQLite ─────────────────────────
@compiles(pgUUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(32)"

from app.main import app
from app.database import Base, get_db

# ── In-memory SQLite for isolation ───────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

engine_test = create_async_engine(
    TEST_DATABASE_URL, echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db

# Disable rate limiting for tests – must disable the actual router-level instances
import app.routers.auth as _auth_mod
import app.routers.entries as _entries_mod
_auth_mod.limiter.enabled = False
_entries_mod.limiter.enabled = False
# Also disable the app-level limiter
from slowapi import Limiter
from slowapi.util import get_remote_address
app.state.limiter.enabled = False


# ── Database lifecycle ───────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Delete rows in explicit order to avoid circular FK (departments ↔ users)
    async with engine_test.begin() as conn:
        from sqlalchemy import text
        # Break circular FK: clear department leader_id first
        await conn.execute(text("UPDATE departments SET leader_id = NULL"))
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        await conn.commit()


# ── Raw DB session for fixtures that insert data directly ────────────
@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


# ── HTTP client ──────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Helper: auth header ─────────────────────────────────────────────
def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Seed admin user directly in DB ──────────────────────────────────
@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    from app.utils.password import hash_password
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash=hash_password("Admin123!"),
        first_name="Test",
        last_name="Admin",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Admin token ─────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user) -> str:
    resp = await client.post("/api/v1/auth/login", json={
        "email": "admin@test.com",
        "password": "Admin123!",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ── Worker user + token ──────────────────────────────────────────────
@pytest_asyncio.fixture
async def worker_user_and_token(client: AsyncClient, admin_token: str):
    """Returns (user_dict, token)."""
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "worker@test.com",
            "password": "Worker123!",
            "first_name": "Test",
            "last_name": "Worker",
            "role": "worker",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    login = await client.post("/api/v1/auth/login", json={
        "email": "worker@test.com",
        "password": "Worker123!",
    })
    assert login.status_code == 200, login.text
    return user_data, login.json()["access_token"]


@pytest_asyncio.fixture
async def worker_token(worker_user_and_token) -> str:
    return worker_user_and_token[1]


@pytest_asyncio.fixture
async def worker_user(worker_user_and_token) -> dict:
    return worker_user_and_token[0]


# ── Department ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def department(client: AsyncClient, admin_token: str) -> dict:
    resp = await client.post(
        "/api/v1/departments",
        json={"name": "Engineering"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Leader user + token (belongs to a department) ────────────────────
@pytest_asyncio.fixture
async def leader_user_and_token(client: AsyncClient, admin_token: str, department: dict):
    """Returns (user_dict, token)."""
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "leader@test.com",
            "password": "Leader123!",
            "first_name": "Test",
            "last_name": "Leader",
            "role": "abteilungsleiter",
            "department_id": department["id"],
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    login = await client.post("/api/v1/auth/login", json={
        "email": "leader@test.com",
        "password": "Leader123!",
    })
    assert login.status_code == 200, login.text
    return user_data, login.json()["access_token"]


@pytest_asyncio.fixture
async def leader_token(leader_user_and_token) -> str:
    return leader_user_and_token[1]


@pytest_asyncio.fixture
async def leader_user(leader_user_and_token) -> dict:
    return leader_user_and_token[0]


# ── Helper functions (importable by test files) ─────────────────────
async def create_schedule_for_user(
    client: AsyncClient, admin_token: str, user_id: str,
    valid_from: str = "2024-01-01",
    mon=480, tue=480, wed=480, thu=480, fri=480, sat=0, sun=0,
):
    resp = await client.put(
        f"/api/v1/schedule/user/{user_id}",
        json={
            "valid_from": valid_from,
            "monday_minutes": mon,
            "tuesday_minutes": tue,
            "wednesday_minutes": wed,
            "thursday_minutes": thu,
            "friday_minutes": fri,
            "saturday_minutes": sat,
            "sunday_minutes": sun,
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


async def create_entry(
    client: AsyncClient, token: str,
    entry_date: str = "2024-06-10",
    start: str = "08:00",
    end: str = "17:00",
    break_min: int = 60,
    description: str = "",
):
    resp = await client.post(
        "/api/v1/entries",
        json={
            "date": entry_date,
            "start_time": start,
            "end_time": end,
            "break_minutes": break_min,
            "description": description,
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_holiday(
    client: AsyncClient, admin_token: str,
    holiday_date: str = "2024-12-25",
    name: str = "Test Holiday",
    is_half_day: bool = False,
):
    resp = await client.post(
        "/api/v1/holidays",
        json={
            "date": holiday_date,
            "name": name,
            "is_half_day": is_half_day,
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def create_absence(
    client: AsyncClient, token: str,
    absence_date: str = "2024-06-15",
    absence_type: str = "urlaub",
    note: str = "",
):
    resp = await client.post(
        "/api/v1/absences",
        json={
            "date": absence_date,
            "type": absence_type,
            "note": note,
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
