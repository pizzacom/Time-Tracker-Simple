"""Tests for PDF, CSV, and Excel export endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_entry, create_schedule_for_user


@pytest.mark.asyncio
class TestPDFExport:
    async def test_export_own_pdf(self, client: AsyncClient,
                                   worker_token: str, worker_user: dict,
                                   admin_token: str):
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        await create_entry(client, worker_token, "2024-06-10")

        resp = await client.get(
            "/api/v1/export/pdf?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 100  # Non-trivial response

    async def test_export_empty_month_pdf(self, client: AsyncClient,
                                           worker_token: str):
        resp = await client.get(
            "/api/v1/export/pdf?year=2024&month=1",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    async def test_admin_exports_user_pdf(self, client: AsyncClient,
                                           admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/export/pdf/{worker_user['id']}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    async def test_worker_cannot_export_others_pdf(self, client: AsyncClient,
                                                    worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/export/pdf/{admin_user.id}?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestCSVExport:
    async def test_export_own_csv(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/export/csv?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        # CSV should contain header line at minimum
        assert len(resp.content) > 10

    async def test_admin_exports_user_csv(self, client: AsyncClient,
                                           admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/export/csv/{worker_user['id']}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


@pytest.mark.asyncio
class TestExcelExport:
    async def test_export_own_excel(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/export/excel?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]
        assert len(resp.content) > 100

    async def test_admin_exports_user_excel(self, client: AsyncClient,
                                             admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/export/excel/{worker_user['id']}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]


@pytest.mark.asyncio
class TestDepartmentExcelExport:
    async def test_admin_exports_dept_excel(self, client: AsyncClient,
                                             admin_token: str, department: dict):
        resp = await client.get(
            f"/api/v1/export/department/{department['id']}/excel?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    async def test_worker_forbidden(self, client: AsyncClient,
                                     worker_token: str, department: dict):
        resp = await client.get(
            f"/api/v1/export/department/{department['id']}/excel?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_nonexistent_dept(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/export/department/{fake_id}/excel?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404
