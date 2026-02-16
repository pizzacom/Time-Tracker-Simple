"""Tests for authentication & authorization endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestHealth:
    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_api_root(self, client: AsyncClient):
        resp = await client.get("/api/v1")
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "Admin123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@test.com"

    async def test_login_wrong_password(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "whatever",
        })
        assert resp.status_code == 401

    async def test_login_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={"email": "x@y.com"})
        assert resp.status_code == 422

    async def test_login_sets_refresh_cookie(self, client: AsyncClient, admin_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "Admin123!",
        })
        assert resp.status_code == 200
        assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
class TestRefresh:
    async def test_refresh_token(self, client: AsyncClient, admin_user):
        login = await client.post("/api/v1/auth/login", json={
            "email": "admin@test.com",
            "password": "Admin123!",
        })
        cookies = login.cookies
        resp = await client.post("/api/v1/auth/refresh", cookies=cookies)
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_without_cookie(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/auth/logout",
                                 headers=auth_header(admin_token))
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestProtectedRoutes:
    async def test_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_invalid_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/me",
                                headers=auth_header("bad.token.here"))
        assert resp.status_code == 401

    async def test_valid_token(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/users/me",
                                headers=auth_header(admin_token))
        assert resp.status_code == 200


@pytest.mark.asyncio
class TestInactiveUser:
    async def test_inactive_user_cannot_login(self, client: AsyncClient, admin_token: str):
        # Create a user, then deactivate
        resp = await client.post("/api/v1/users", json={
            "email": "inactive@test.com",
            "password": "Inactive123!",
            "first_name": "In",
            "last_name": "Active",
            "role": "worker",
        }, headers=auth_header(admin_token))
        user_id = resp.json()["id"]

        # Deactivate
        await client.delete(f"/api/v1/users/{user_id}",
                            headers=auth_header(admin_token))

        # Try login
        resp = await client.post("/api/v1/auth/login", json={
            "email": "inactive@test.com",
            "password": "Inactive123!",
        })
        assert resp.status_code in (401, 403)
