"""Tests for time entry CRUD, date filtering, and overtime recalculation."""
import pytest
import uuid
from httpx import AsyncClient
from tests.conftest import auth_header, create_entry, create_schedule_for_user


@pytest.mark.asyncio
class TestCreateEntry:
    async def test_create_basic_entry(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/entries", json={
            "date": "2024-06-10",
            "start_time": "08:00",
            "end_time": "17:00",
            "break_minutes": 60,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["work_minutes"] == 480
        assert data["entry_type"] == "regular"
        assert "id" in data
        assert "user_id" in data

    async def test_create_entry_with_description(self, client: AsyncClient,
                                                  worker_token: str):
        entry = await create_entry(client, worker_token, description="Project X")
        assert entry["description"] == "Project X"

    async def test_create_entry_no_break(self, client: AsyncClient, worker_token: str):
        entry = await create_entry(client, worker_token,
                                   start="09:00", end="12:00", break_min=0)
        assert entry["work_minutes"] == 180

    async def test_create_entry_invalid_times(self, client: AsyncClient,
                                               worker_token: str):
        """End before start should return 400 (work_minutes <= 0)."""
        resp = await client.post("/api/v1/entries", json={
            "date": "2024-06-10",
            "start_time": "17:00",
            "end_time": "08:00",
            "break_minutes": 0,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 400

    async def test_create_entry_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/entries", json={
            "date": "2024-06-10",
            "start_time": "08:00",
            "end_time": "17:00",
            "break_minutes": 0,
        })
        assert resp.status_code == 401

    async def test_create_entry_missing_fields(self, client: AsyncClient,
                                                worker_token: str):
        resp = await client.post("/api/v1/entries", json={
            "date": "2024-06-10",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestListEntries:
    async def test_list_own_entries(self, client: AsyncClient, worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-06-10")
        await create_entry(client, worker_token, entry_date="2024-06-11")

        resp = await client.get("/api/v1/entries", headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_entries_are_user_scoped(self, client: AsyncClient,
                                           admin_token: str, worker_token: str):
        """Admin and worker create entries; each sees only their own."""
        await create_entry(client, admin_token, entry_date="2024-06-10")
        await create_entry(client, worker_token, entry_date="2024-06-10")

        admin_entries = await client.get("/api/v1/entries",
                                         headers=auth_header(admin_token))
        worker_entries = await client.get("/api/v1/entries",
                                          headers=auth_header(worker_token))
        assert len(admin_entries.json()) == 1
        assert len(worker_entries.json()) == 1


@pytest.mark.asyncio
class TestDateFiltering:
    """Crucial bug-regression tests: date_from / date_to must filter."""

    async def test_filter_by_date_from(self, client: AsyncClient, worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-06-01")
        await create_entry(client, worker_token, entry_date="2024-06-15")
        await create_entry(client, worker_token, entry_date="2024-06-30")

        resp = await client.get("/api/v1/entries?date_from=2024-06-10",
                                headers=auth_header(worker_token))
        dates = [e["date"] for e in resp.json()]
        assert "2024-06-01" not in dates
        assert "2024-06-15" in dates
        assert "2024-06-30" in dates

    async def test_filter_by_date_to(self, client: AsyncClient, worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-06-01")
        await create_entry(client, worker_token, entry_date="2024-06-15")
        await create_entry(client, worker_token, entry_date="2024-06-30")

        resp = await client.get("/api/v1/entries?date_to=2024-06-20",
                                headers=auth_header(worker_token))
        dates = [e["date"] for e in resp.json()]
        assert "2024-06-01" in dates
        assert "2024-06-15" in dates
        assert "2024-06-30" not in dates

    async def test_filter_exact_date(self, client: AsyncClient, worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-06-10")
        await create_entry(client, worker_token, entry_date="2024-06-11")
        await create_entry(client, worker_token, entry_date="2024-06-12")

        resp = await client.get(
            "/api/v1/entries?date_from=2024-06-11&date_to=2024-06-11",
            headers=auth_header(worker_token),
        )
        entries = resp.json()
        assert len(entries) == 1
        assert entries[0]["date"] == "2024-06-11"

    async def test_no_filter_returns_all(self, client: AsyncClient, worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-01-01")
        await create_entry(client, worker_token, entry_date="2024-12-31")

        resp = await client.get("/api/v1/entries",
                                headers=auth_header(worker_token))
        assert len(resp.json()) == 2


@pytest.mark.asyncio
class TestUpdateEntry:
    async def test_update_entry_times(self, client: AsyncClient, worker_token: str):
        entry = await create_entry(client, worker_token)
        entry_id = entry["id"]

        resp = await client.put(f"/api/v1/entries/{entry_id}", json={
            "start_time": "09:00",
            "end_time": "18:00",
            "break_minutes": 30,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert resp.json()["work_minutes"] == 510  # 9h - 30min

    async def test_update_entry_description(self, client: AsyncClient,
                                            worker_token: str):
        entry = await create_entry(client, worker_token)
        resp = await client.put(f"/api/v1/entries/{entry['id']}", json={
            "description": "Updated description",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated description"

    async def test_update_entry_date(self, client: AsyncClient, worker_token: str):
        entry = await create_entry(client, worker_token, entry_date="2024-06-10")
        resp = await client.put(f"/api/v1/entries/{entry['id']}", json={
            "date": "2024-06-20",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200, resp.text
        assert resp.json()["date"] == "2024-06-20"

    async def test_update_nonexistent_entry(self, client: AsyncClient,
                                             worker_token: str):
        fake_id = str(uuid.uuid4())
        resp = await client.put(f"/api/v1/entries/{fake_id}", json={
            "description": "Ghost",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 404

    async def test_update_other_users_entry(self, client: AsyncClient,
                                            admin_token: str, worker_token: str):
        """Admin creates entry; worker tries to update it — should 404."""
        entry = await create_entry(client, admin_token)
        resp = await client.put(f"/api/v1/entries/{entry['id']}", json={
            "description": "Hacked",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 404

    async def test_update_with_empty_strings(self, client: AsyncClient,
                                             worker_token: str):
        """Regression: empty strings should be coerced to None, not cause errors."""
        entry = await create_entry(client, worker_token, description="Original")
        resp = await client.put(f"/api/v1/entries/{entry['id']}", json={
            "description": "",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestDeleteEntry:
    async def test_delete_own_entry(self, client: AsyncClient, worker_token: str):
        entry = await create_entry(client, worker_token)
        resp = await client.delete(f"/api/v1/entries/{entry['id']}",
                                    headers=auth_header(worker_token))
        assert resp.status_code == 200

        # Verify gone
        entries = await client.get("/api/v1/entries",
                                   headers=auth_header(worker_token))
        assert len(entries.json()) == 0

    async def test_delete_other_users_entry(self, client: AsyncClient,
                                            admin_token: str, worker_token: str):
        entry = await create_entry(client, admin_token)
        resp = await client.delete(f"/api/v1/entries/{entry['id']}",
                                    headers=auth_header(worker_token))
        assert resp.status_code == 404

    async def test_delete_nonexistent(self, client: AsyncClient, worker_token: str):
        resp = await client.delete(f"/api/v1/entries/{uuid.uuid4()}",
                                    headers=auth_header(worker_token))
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestAdminViewEntries:
    async def test_admin_views_user_entries(self, client: AsyncClient,
                                            admin_token: str,
                                            worker_user: dict,
                                            worker_token: str):
        await create_entry(client, worker_token, entry_date="2024-06-10")
        resp = await client.get(
            f"/api/v1/entries/user/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_worker_cannot_view_others(self, client: AsyncClient,
                                              worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/entries/user/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403
