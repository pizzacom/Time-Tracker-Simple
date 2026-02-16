"""Tests for /api/v1/timer endpoints (server-side timer persistence)."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── GET /timer – no running timer ─────────────────────────────────────

class TestGetTimer:
    async def test_no_timer(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/timer", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_running"] is False
        assert data["start_time"] is None
        assert data["description"] is None

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/timer")
        assert resp.status_code == 401


# ── PUT /timer – start / update timer ─────────────────────────────────

class TestPutTimer:
    async def test_start_timer(self, client: AsyncClient, worker_token):
        resp = await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z", "description": "Coding"},
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_running"] is True
        assert "2024-06-15" in data["start_time"]
        assert data["description"] == "Coding"

    async def test_update_timer(self, client: AsyncClient, worker_token):
        # Start
        await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z", "description": "Task A"},
            headers=auth_header(worker_token),
        )
        # Update
        resp = await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T09:00:00Z", "description": "Task B"},
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Task B"
        assert "09:00" in data["start_time"]

    async def test_start_timer_no_description(self, client: AsyncClient, worker_token):
        resp = await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z"},
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] is None

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z"},
        )
        assert resp.status_code == 401


# ── DELETE /timer – stop / clear timer ─────────────────────────────────

class TestDeleteTimer:
    async def test_clear_running_timer(self, client: AsyncClient, worker_token):
        # Start
        await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z", "description": "Work"},
            headers=auth_header(worker_token),
        )
        # Delete
        resp = await client.delete("/api/v1/timer", headers=auth_header(worker_token))
        assert resp.status_code == 200

        # Should be empty now
        get_resp = await client.get("/api/v1/timer", headers=auth_header(worker_token))
        assert get_resp.json()["is_running"] is False

    async def test_clear_no_timer(self, client: AsyncClient, worker_token):
        """Clearing when no timer exists should not error."""
        resp = await client.delete("/api/v1/timer", headers=auth_header(worker_token))
        assert resp.status_code == 200

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.delete("/api/v1/timer")
        assert resp.status_code == 401


# ── Cross-user isolation ──────────────────────────────────────────────

class TestTimerIsolation:
    async def test_timers_are_per_user(self, client: AsyncClient, admin_token, worker_token):
        """Admin and worker timers are independent."""
        # Admin starts timer
        await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T08:00:00Z", "description": "Admin stuff"},
            headers=auth_header(admin_token),
        )
        # Worker should have no timer
        resp = await client.get("/api/v1/timer", headers=auth_header(worker_token))
        assert resp.json()["is_running"] is False

        # Worker starts timer
        await client.put(
            "/api/v1/timer",
            json={"start_time": "2024-06-15T09:00:00Z", "description": "Worker stuff"},
            headers=auth_header(worker_token),
        )

        # Admin timer should still show admin's timer
        resp = await client.get("/api/v1/timer", headers=auth_header(admin_token))
        assert resp.json()["description"] == "Admin stuff"

        # Worker timer should show worker's timer
        resp = await client.get("/api/v1/timer", headers=auth_header(worker_token))
        assert resp.json()["description"] == "Worker stuff"
