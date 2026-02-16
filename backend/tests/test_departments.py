"""Tests for department CRUD."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


@pytest.mark.asyncio
class TestListDepartments:
    async def test_admin_lists_departments(self, client: AsyncClient,
                                           admin_token: str, department: dict):
        resp = await client.get(
            "/api/v1/departments",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        depts = resp.json()
        assert len(depts) >= 1
        assert any(d["name"] == "Engineering" for d in depts)

    async def test_worker_forbidden(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/departments",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestCreateDepartment:
    async def test_admin_creates_department(self, client: AsyncClient, admin_token: str):
        resp = await client.post("/api/v1/departments", json={
            "name": "Sales",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "Sales"
        assert resp.json()["member_count"] == 0

    async def test_duplicate_name_409(self, client: AsyncClient, admin_token: str):
        await client.post("/api/v1/departments", json={
            "name": "Marketing",
        }, headers=auth_header(admin_token))

        resp = await client.post("/api/v1/departments", json={
            "name": "Marketing",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 409

    async def test_worker_cannot_create(self, client: AsyncClient, worker_token: str):
        resp = await client.post("/api/v1/departments", json={
            "name": "Illegal",
        }, headers=auth_header(worker_token))
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestUpdateDepartment:
    async def test_admin_updates_department(self, client: AsyncClient,
                                            admin_token: str, department: dict):
        resp = await client.put(
            f"/api/v1/departments/{department['id']}",
            json={"name": "Engineering v2"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Engineering v2"

    async def test_nonexistent_404(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.put(
            f"/api/v1/departments/{fake_id}",
            json={"name": "Nope"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestDeleteDepartment:
    async def test_delete_empty_department(self, client: AsyncClient, admin_token: str):
        # Create a fresh department  with no members
        create = await client.post("/api/v1/departments", json={
            "name": "ToDelete",
        }, headers=auth_header(admin_token))
        dept_id = create.json()["id"]

        resp = await client.delete(
            f"/api/v1/departments/{dept_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    async def test_delete_department_with_members_409(self, client: AsyncClient,
                                                      admin_token: str,
                                                      department: dict):
        # Add a member to the department
        await client.post("/api/v1/users", json={
            "email": "deptworker@test.com",
            "password": "Worker123!",
            "first_name": "Dept",
            "last_name": "Worker",
            "role": "worker",
            "department_id": department["id"],
        }, headers=auth_header(admin_token))

        resp = await client.delete(
            f"/api/v1/departments/{department['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 409
        assert "member" in resp.json()["detail"].lower()

    async def test_worker_cannot_delete(self, client: AsyncClient,
                                         worker_token: str, department: dict):
        resp = await client.delete(
            f"/api/v1/departments/{department['id']}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403
