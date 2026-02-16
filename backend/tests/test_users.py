"""Tests for user management endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestGetMe:
    async def test_admin_get_me(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/users/me", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
        assert "overtime_balance_minutes" in data

    async def test_worker_get_me(self, client: AsyncClient, worker_token: str):
        resp = await client.get("/api/v1/users/me", headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "worker"


@pytest.mark.asyncio
class TestUpdateProfile:
    async def test_update_own_name(self, client: AsyncClient, worker_token: str):
        resp = await client.put("/api/v1/users/me", json={
            "first_name": "Updated",
            "last_name": "Name",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"


@pytest.mark.asyncio
class TestListUsers:
    async def test_admin_lists_users(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/users", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_worker_cannot_list(self, client: AsyncClient, worker_token: str):
        resp = await client.get("/api/v1/users", headers=auth_header(worker_token))
        assert resp.status_code == 403

    async def test_leader_lists_own_dept_only(self, client, admin_token, department,
                                               leader_token):
        # Create worker in same dept
        await client.post("/api/v1/users", json={
            "email": "w2@test.com", "password": "Worker123!", "first_name": "W",
            "last_name": "Two", "role": "worker", "department_id": department["id"],
        }, headers=auth_header(admin_token))

        # Create worker in NO dept
        await client.post("/api/v1/users", json={
            "email": "w3@test.com", "password": "Worker123!", "first_name": "W",
            "last_name": "NoDept", "role": "worker",
        }, headers=auth_header(admin_token))

        resp = await client.get("/api/v1/users", headers=auth_header(leader_token))
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        # Leader should see own dept members (including self)
        assert "leader@test.com" in emails
        assert "w2@test.com" in emails
        # Should NOT see users outside dept
        assert "w3@test.com" not in emails


@pytest.mark.asyncio
class TestCreateUser:
    async def test_admin_creates_worker(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "new@test.com",
            "password": "NewUser123!",
            "first_name": "New",
            "last_name": "User",
            "role": "worker",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        assert resp.json()["email"] == "new@test.com"

    async def test_duplicate_email_rejected(self, client: AsyncClient, admin_token: str):
        await client.post("/api/v1/users", json={
            "email": "dup@test.com", "password": "Dup123!",
            "first_name": "D", "last_name": "Up", "role": "worker",
        }, headers=auth_header(admin_token))

        resp = await client.post("/api/v1/users", json={
            "email": "dup@test.com", "password": "Other123!",
            "first_name": "D", "last_name": "Up2", "role": "worker",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 409

    async def test_worker_cannot_create_user(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "hack@test.com", "password": "Hack123!",
            "first_name": "H", "last_name": "Ack", "role": "worker",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 403

    async def test_missing_required_fields(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "incomplete@test.com",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestUpdateUser:
    async def test_admin_updates_user(self, client: AsyncClient, admin_token: str,
                                      worker_user: dict):
        resp = await client.put(
            f"/api/v1/users/{worker_user['id']}",
            json={"first_name": "Changed"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Changed"

    async def test_update_nonexistent_user(self, client: AsyncClient, admin_token: str):
        import uuid
        fake_id = str(uuid.uuid4())
        resp = await client.put(
            f"/api/v1/users/{fake_id}",
            json={"first_name": "Ghost"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    async def test_admin_updates_email(self, client: AsyncClient, admin_token: str,
                                       worker_user: dict):
        resp = await client.put(
            f"/api/v1/users/{worker_user['id']}",
            json={"email": "newemail@test.com"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "newemail@test.com"

    async def test_update_email_rejects_duplicate(self, client: AsyncClient, admin_token: str,
                                                   worker_user: dict):
        # admin@test.com already exists
        resp = await client.put(
            f"/api/v1/users/{worker_user['id']}",
            json={"email": "admin@test.com"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 409

    async def test_update_email_rejects_invalid(self, client: AsyncClient, admin_token: str,
                                                 worker_user: dict):
        resp = await client.put(
            f"/api/v1/users/{worker_user['id']}",
            json={"email": "notavalidemail"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestEmailValidation:
    async def test_create_user_invalid_email_rejected(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "testsoll",
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "worker",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 422

    async def test_create_user_no_at_rejected(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "no-at-sign",
            "password": "Test123!",
            "first_name": "T",
            "last_name": "U",
            "role": "worker",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 422

    async def test_create_user_valid_email_accepted(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/users", json={
            "email": "valid@example.com",
            "password": "Test123!",
            "first_name": "Valid",
            "last_name": "User",
            "role": "worker",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_admin_deactivates_user(self, client: AsyncClient, admin_token: str,
                                          worker_user: dict):
        resp = await client.delete(
            f"/api/v1/users/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

        # Verify user is deactivated (still in list but inactive)
        users = await client.get("/api/v1/users?is_active=false",
                                 headers=auth_header(admin_token))
        deactivated = [u for u in users.json() if u["id"] == worker_user["id"]]
        assert len(deactivated) == 1
        assert deactivated[0]["is_active"] is False

    async def test_worker_cannot_delete(self, client: AsyncClient, worker_token: str,
                                        admin_user):
        resp = await client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestHardDeleteUser:
    async def test_admin_hard_deletes_user(self, client: AsyncClient, admin_token: str):
        # Create a disposable user to delete
        create_resp = await client.post("/api/v1/users", json={
            "email": "disposable@test.com", "password": "Dispose123!",
            "first_name": "Disposable", "last_name": "User", "role": "worker",
        }, headers=auth_header(admin_token))
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        # Hard delete
        resp = await client.delete(
            f"/api/v1/users/{user_id}/permanent",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "permanently" in resp.json()["message"].lower()

        # Verify user is gone (not even in inactive list)
        users_resp = await client.get("/api/v1/users", headers=auth_header(admin_token))
        ids = [u["id"] for u in users_resp.json()]
        assert user_id not in ids

    async def test_cannot_hard_delete_self(self, client: AsyncClient, admin_token: str,
                                           admin_user):
        resp = await client.delete(
            f"/api/v1/users/{admin_user.id}/permanent",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400

    async def test_worker_cannot_hard_delete(self, client: AsyncClient, worker_token: str,
                                             worker_user: dict):
        resp = await client.delete(
            f"/api/v1/users/{worker_user['id']}/permanent",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_hard_delete_nonexistent(self, client: AsyncClient, admin_token: str):
        import uuid
        fake_id = str(uuid.uuid4())
        resp = await client.delete(
            f"/api/v1/users/{fake_id}/permanent",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404
