"""Tests for holiday CRUD and auto-generation."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestGetHolidays:
    async def test_get_holidays_empty(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/holidays?year=2024",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
class TestCreateHoliday:
    async def test_admin_creates_holiday(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/holidays", json={
            "date": "2024-12-25",
            "name": "Christmas",
            "is_half_day": False,
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "Christmas"
        assert resp.json()["date"] == "2024-12-25"

    async def test_create_half_day_holiday(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/holidays", json={
            "date": "2024-12-24",
            "name": "Heiligabend",
            "is_half_day": True,
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        assert resp.json()["is_half_day"] is True

    async def test_duplicate_date_409(self, client: AsyncClient, admin_token: str):
        await client.post("/api/v1/holidays", json={
            "date": "2024-01-01",
            "name": "Neujahr",
        }, headers=auth_header(admin_token))

        resp = await client.post("/api/v1/holidays", json={
            "date": "2024-01-01",
            "name": "Neujahr Duplicate",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 409

    async def test_worker_cannot_create(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/holidays", json={
            "date": "2024-05-01",
            "name": "Tag der Arbeit",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDeleteHoliday:
    async def test_admin_deletes_holiday(self, client: AsyncClient, admin_token: str):
        create = await client.post("/api/v1/holidays", json={
            "date": "2024-11-01",
            "name": "ToDelete",
        }, headers=auth_header(admin_token))
        holiday_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/holidays/{holiday_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    async def test_delete_nonexistent(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(
            f"/api/v1/holidays/{fake_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    async def test_worker_cannot_delete(self, client: AsyncClient,
                                         worker_token: str, admin_token: str):
        create = await client.post("/api/v1/holidays", json={
            "date": "2024-10-03",
            "name": "Tag der Einheit",
        }, headers=auth_header(admin_token))
        holiday_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/holidays/{holiday_id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestAutoGenerateHolidays:
    async def test_auto_generate_german_holidays(self, client: AsyncClient,
                                                  admin_token: str):
        resp = await client.post(
            "/api/v1/holidays/auto-generate?year=2025",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201
        holidays = resp.json()
        assert len(holidays) >= 8  # 9 standard German holidays, some may already exist
        names = [h["name"] for h in holidays]
        assert "Neujahr" in names
        assert "Karfreitag" in names
        assert "Ostermontag" in names

    async def test_auto_generate_idempotent(self, client: AsyncClient,
                                             admin_token: str):
        """Running auto-generate twice should skip existing holidays."""
        await client.post(
            "/api/v1/holidays/auto-generate?year=2025",
            headers=auth_header(admin_token),
        )
        resp2 = await client.post(
            "/api/v1/holidays/auto-generate?year=2025",
            headers=auth_header(admin_token),
        )
        assert resp2.status_code == 201
        assert len(resp2.json()) == 0  # All already exist

    async def test_worker_cannot_auto_generate(self, client: AsyncClient,
                                                worker_token: str):
        resp = await client.post(
            "/api/v1/holidays/auto-generate?year=2025",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403
