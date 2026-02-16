"""Tests for change password and backup/restore endpoints."""
import json

import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestChangePassword:
    async def test_change_password_success(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Admin123!",
            "new_password": "NewAdmin456!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["message"] == "Password changed successfully"

        # Can login with new password
        login = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "NewAdmin456!",
        })
        assert login.status_code == 200

    async def test_change_password_wrong_current(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "WrongPassword!",
            "new_password": "NewAdmin456!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    async def test_change_password_too_short(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Admin123!",
            "new_password": "ab",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 422  # pydantic validation

    async def test_change_password_same_as_current(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Admin123!",
            "new_password": "Admin123!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "differ" in resp.json()["detail"].lower()

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Admin123!",
            "new_password": "NewAdmin456!",
        })
        assert resp.status_code == 401

    async def test_worker_can_change_password(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Worker123!",
            "new_password": "NewWorker456!",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200

        # Can login with new password
        login = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.com",
            "password": "NewWorker456!",
        })
        assert login.status_code == 200


@pytest.mark.asyncio
class TestBackupExport:
    async def test_export_backup(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/backup/export",
                                headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"

        data = resp.json()
        assert "version" in data
        assert "tables" in data
        assert "users" in data["tables"]
        assert "departments" in data["tables"]

    async def test_export_requires_admin(self, client: AsyncClient, worker_token: str):
        resp = await client.get("/api/v1/backup/export",
                                headers=auth_header(worker_token))
        assert resp.status_code == 403

    async def test_export_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/backup/export")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestBackupImport:
    async def test_import_backup_roundtrip(self, client: AsyncClient, admin_token: str):
        # Create some data first
        await client.post("/api/v1/holidays", json={
            "date": "2025-12-25",
            "name": "Weihnachten",
        }, headers=auth_header(admin_token))

        # Export
        export_resp = await client.get("/api/v1/backup/export",
                                       headers=auth_header(admin_token))
        assert export_resp.status_code == 200
        backup_data = export_resp.json()

        # Verify holiday in backup
        holidays = backup_data["tables"]["holidays"]
        assert any(h["name"] == "Weihnachten" for h in holidays)

        # Import (restore) — use multipart file upload
        backup_bytes = json.dumps(backup_data).encode("utf-8")
        resp = await client.post(
            "/api/v1/backup/import",
            files={"file": ("backup.json", backup_bytes, "application/json")},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "restored" in resp.json()["message"].lower()

    async def test_import_requires_admin(self, client: AsyncClient, worker_token: str):
        backup_bytes = json.dumps({"tables": {}}).encode("utf-8")
        resp = await client.post(
            "/api/v1/backup/import",
            files={"file": ("backup.json", backup_bytes, "application/json")},
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_import_invalid_json(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/backup/import",
            files={"file": ("backup.json", b"not json", "application/json")},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400

    async def test_import_missing_tables_key(self, client: AsyncClient, admin_token: str):
        backup_bytes = json.dumps({"foo": "bar"}).encode("utf-8")
        resp = await client.post(
            "/api/v1/backup/import",
            files={"file": ("backup.json", backup_bytes, "application/json")},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400
        assert "missing" in resp.json()["detail"].lower()

    async def test_import_wrong_file_extension(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/backup/import",
            files={"file": ("backup.txt", b"{}", "text/plain")},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400
