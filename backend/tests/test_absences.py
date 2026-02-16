"""Tests for absence management and vacation budget."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestCreateAbsence:
    async def test_create_urlaub(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-15",
            "type": "urlaub",
            "note": "Vacation day",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "urlaub"
        assert data["date"] == "2024-06-15"

    async def test_create_krank(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-16",
            "type": "krank",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        assert resp.json()["type"] == "krank"

    async def test_create_sonderurlaub(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-17",
            "type": "sonderurlaub",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201
        assert resp.json()["type"] == "sonderurlaub"

    async def test_duplicate_date_409(self, client: AsyncClient, worker_token: str):
        await client.post("/api/v1/absences", json={
            "date": "2024-06-20",
            "type": "urlaub",
        }, headers=auth_header(worker_token))

        resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-20",
            "type": "krank",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 409

    async def test_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-15",
            "type": "urlaub",
        })
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestListAbsences:
    async def test_list_own_absences(self, client: AsyncClient, worker_token: str):
        await client.post("/api/v1/absences", json={
            "date": "2024-06-10",
            "type": "urlaub",
        }, headers=auth_header(worker_token))

        resp = await client.get(
            "/api/v1/absences?year=2024",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_filter_by_type(self, client: AsyncClient, worker_token: str):
        await client.post("/api/v1/absences", json={
            "date": "2024-06-10",
            "type": "urlaub",
        }, headers=auth_header(worker_token))
        await client.post("/api/v1/absences", json={
            "date": "2024-06-11",
            "type": "krank",
        }, headers=auth_header(worker_token))

        resp = await client.get(
            "/api/v1/absences?year=2024&type=krank",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        for a in resp.json():
            assert a["type"] == "krank"


@pytest.mark.asyncio
class TestDeleteAbsence:
    async def test_delete_own_absence(self, client: AsyncClient, worker_token: str):
        create_resp = await client.post("/api/v1/absences", json={
            "date": "2024-06-25",
            "type": "urlaub",
        }, headers=auth_header(worker_token))
        absence_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/absences/{absence_id}",
            headers=auth_header(worker_token),
        )
        assert del_resp.status_code == 200

    async def test_delete_nonexistent(self, client: AsyncClient, worker_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(
            f"/api/v1/absences/{fake_id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestAdminViewAbsences:
    async def test_admin_views_user_absences(self, client: AsyncClient,
                                              admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/absences/user/{worker_user['id']}?year=2024",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_worker_cannot_view_others(self, client: AsyncClient,
                                              worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/absences/user/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestVacationBudget:
    async def test_get_own_budget(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/absences/vacation-budget?year=2024",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_days" in data
        assert "used_days" in data
        assert "remaining_days" in data
        assert data["used_days"] == 0

    async def test_vacation_budget_updates_on_absence(self, client: AsyncClient,
                                                       worker_token: str):
        # Create a vacation absence
        await client.post("/api/v1/absences", json={
            "date": "2024-06-10",
            "type": "urlaub",
        }, headers=auth_header(worker_token))

        resp = await client.get(
            "/api/v1/absences/vacation-budget?year=2024",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.json()["used_days"] == 1

    async def test_admin_sets_budget(self, client: AsyncClient,
                                      admin_token: str, worker_user: dict):
        resp = await client.put(
            f"/api/v1/absences/vacation-budget/{worker_user['id']}?year=2024",
            json={"total_days": 25},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total_days"] == 25
