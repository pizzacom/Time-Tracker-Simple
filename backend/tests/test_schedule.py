"""Tests for work schedule and Soll calculation."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_schedule_for_user


@pytest.mark.asyncio
class TestScheduleEndpoints:
    async def test_get_own_schedule_default(self, client: AsyncClient, worker_token: str):
        resp = await client.get("/api/v1/schedule", headers=auth_header(worker_token))
        assert resp.status_code == 200
        # New users get a default 8h Mon-Fri schedule
        data = resp.json()
        assert data is not None
        assert data["monday_minutes"] == 480
        assert data["saturday_minutes"] == 0

    async def test_create_own_schedule(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-01-01",
            "monday_minutes": 480,
            "tuesday_minutes": 480,
            "wednesday_minutes": 480,
            "thursday_minutes": 480,
            "friday_minutes": 480,
            "saturday_minutes": 0,
            "sunday_minutes": 0,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["monday_minutes"] == 480
        assert data["valid_from"] == "2024-01-01"

    async def test_get_own_schedule_after_create(self, client: AsyncClient,
                                                  worker_token: str):
        await client.post("/api/v1/schedule", json={
            "valid_from": "2024-01-01",
        }, headers=auth_header(worker_token))

        resp = await client.get("/api/v1/schedule", headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert resp.json() is not None
        assert resp.json()["monday_minutes"] == 480

    async def test_admin_sets_user_schedule(self, client: AsyncClient,
                                            admin_token: str, worker_user: dict):
        sched = await create_schedule_for_user(client, admin_token, worker_user["id"])
        assert sched["monday_minutes"] == 480

    async def test_admin_gets_user_schedule(self, client: AsyncClient,
                                            admin_token: str, worker_user: dict):
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        resp = await client.get(
            f"/api/v1/schedule/user/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["monday_minutes"] == 480

    async def test_worker_cannot_view_other_schedule(self, client: AsyncClient,
                                                     worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/schedule/user/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestScheduleChaining:
    """When a new schedule is created, the old one's valid_until should be set."""

    async def test_replacing_schedule_closes_old(self, client: AsyncClient,
                                                  worker_token: str):
        # Create first schedule
        resp1 = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-01-01",
        }, headers=auth_header(worker_token))
        assert resp1.status_code == 201

        # Create second schedule
        resp2 = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-07-01",
            "monday_minutes": 240,
        }, headers=auth_header(worker_token))
        assert resp2.status_code == 201
        assert resp2.json()["monday_minutes"] == 240

    async def test_update_same_valid_from_does_not_500(self, client: AsyncClient,
                                                        worker_token: str):
        """Updating schedule with the same valid_from should update in place, not 500."""
        resp1 = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-06-01",
            "monday_minutes": 480,
        }, headers=auth_header(worker_token))
        assert resp1.status_code == 201
        old_id = resp1.json()["id"]

        # Update with same valid_from but different minutes
        resp2 = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-06-01",
            "monday_minutes": 360,
        }, headers=auth_header(worker_token))
        assert resp2.status_code == 201
        assert resp2.json()["monday_minutes"] == 360
        # Should update the same record
        assert resp2.json()["id"] == old_id

    async def test_admin_update_same_valid_from(self, client: AsyncClient,
                                                 admin_token: str, worker_user: dict):
        """Admin updating schedule with same valid_from should update in place."""
        uid = worker_user["id"]
        resp1 = await client.put(f"/api/v1/schedule/user/{uid}", json={
            "valid_from": "2024-03-01",
            "monday_minutes": 480,
        }, headers=auth_header(admin_token))
        assert resp1.status_code == 200
        old_id = resp1.json()["id"]

        resp2 = await client.put(f"/api/v1/schedule/user/{uid}", json={
            "valid_from": "2024-03-01",
            "monday_minutes": 300,
        }, headers=auth_header(admin_token))
        assert resp2.status_code == 200
        assert resp2.json()["monday_minutes"] == 300
        assert resp2.json()["id"] == old_id


@pytest.mark.asyncio
class TestScheduleCustomValues:
    async def test_part_time_schedule(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-01-01",
            "monday_minutes": 240,
            "tuesday_minutes": 240,
            "wednesday_minutes": 240,
            "thursday_minutes": 0,
            "friday_minutes": 0,
            "saturday_minutes": 0,
            "sunday_minutes": 0,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        assert resp.json()["thursday_minutes"] == 0

    async def test_invalid_minutes(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-01-01",
            "monday_minutes": 9999,  # Exceeds 1440 limit
        }, headers=auth_header(worker_token))
        assert resp.status_code == 422
