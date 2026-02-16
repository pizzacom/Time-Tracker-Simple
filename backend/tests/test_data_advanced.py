"""Advanced tests for /api/v1/data endpoints.

Covers:
- Admin/leader export for other users
- Admin/leader import for other users
- Department access restrictions for leaders
- Default work schedule on user creation
- Schedule backfill for existing users
"""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_entry, create_absence


pytestmark = pytest.mark.anyio


# ── Helpers ──────────────────────────────────────────────────────────

async def _create_dept_worker(client, admin_token, department):
    """Create a worker in the given department and return (user_dict, token)."""
    resp = await client.post(
        "/api/v1/users",
        json={
            "email": "deptworker@test.com",
            "password": "Worker123!",
            "first_name": "Dept",
            "last_name": "Worker",
            "role": "worker",
            "department_id": department["id"],
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201, resp.text
    user_data = resp.json()

    login = await client.post("/api/v1/auth/login", json={
        "email": "deptworker@test.com",
        "password": "Worker123!",
    })
    assert login.status_code == 200, login.text
    return user_data, login.json()["access_token"]


# ── Export for other users ───────────────────────────────────────────

class TestExportForOtherUsers:
    async def test_admin_exports_worker_data(
        self, client: AsyncClient, admin_token: str, worker_user: dict, worker_token: str,
    ):
        """Admin can export any user's data."""
        await create_entry(client, worker_token, entry_date="2024-03-10")
        await create_absence(client, worker_token, absence_date="2024-03-15")

        resp = await client.get(
            f"/api/v1/data/export/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == 1
        assert len(data["entries"]) == 1
        assert len(data["absences"]) == 1
        assert data["user"]["email"] == "worker@test.com"

    async def test_leader_exports_dept_member(
        self, client: AsyncClient, admin_token: str, leader_token: str, department: dict,
    ):
        """Leader can export data for users in their department."""
        user_data, token = await _create_dept_worker(client, admin_token, department)
        await create_entry(client, token, entry_date="2024-04-01")

        resp = await client.get(
            f"/api/v1/data/export/{user_data['id']}",
            headers=auth_header(leader_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["entries"]) == 1

    async def test_leader_cannot_export_outside_dept(
        self, client: AsyncClient, leader_token: str, worker_user: dict,
    ):
        """Leader cannot export data for users outside their department."""
        resp = await client.get(
            f"/api/v1/data/export/{worker_user['id']}",
            headers=auth_header(leader_token),
        )
        assert resp.status_code == 403

    async def test_worker_cannot_export_others(
        self, client: AsyncClient, worker_token: str, admin_user,
    ):
        """Workers cannot access the export-for-user endpoint."""
        resp = await client.get(
            f"/api/v1/data/export/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_export_nonexistent_user(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/data/export/{fake_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    async def test_export_includes_all_months(
        self, client: AsyncClient, worker_token: str,
    ):
        """Export is a full backup – contains data from multiple months."""
        await create_entry(client, worker_token, entry_date="2024-01-15")
        await create_entry(client, worker_token, entry_date="2024-06-10")
        await create_entry(client, worker_token, entry_date="2024-12-20")

        resp = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        data = resp.json()
        dates = [e["date"] for e in data["entries"]]
        assert "2024-01-15" in dates
        assert "2024-06-10" in dates
        assert "2024-12-20" in dates


# ── Import for other users ───────────────────────────────────────────

class TestImportForOtherUsers:
    async def test_admin_imports_for_worker_merge(
        self, client: AsyncClient, admin_token: str, worker_user: dict, worker_token: str,
    ):
        """Admin can import data for any user in merge mode."""
        payload = {
            "entries": [
                {"date": "2024-05-01", "start_time": "08:00:00", "end_time": "16:00:00",
                 "break_minutes": 30, "description": "admin-imported"},
            ],
            "absences": [
                {"date": "2024-05-02", "type": "krank", "note": "admin note"},
            ],
        }
        resp = await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=merge",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries_imported"] == 1
        assert data["absences_imported"] == 1

        # Verify data is visible to the worker
        export = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        export_data = export.json()
        assert any(e["description"] == "admin-imported" for e in export_data["entries"])
        assert any(a["note"] == "admin note" for a in export_data["absences"])

    async def test_admin_imports_for_worker_replace(
        self, client: AsyncClient, admin_token: str, worker_user: dict, worker_token: str,
    ):
        """Admin can import data for user in replace mode, clearing existing data."""
        # Create existing data for worker
        await create_entry(client, worker_token, entry_date="2024-03-01")
        await create_absence(client, worker_token, absence_date="2024-03-05")

        # Replace with new data
        payload = {
            "entries": [
                {"date": "2024-09-01", "start_time": "09:00:00", "end_time": "17:00:00",
                 "break_minutes": 0, "description": "replaced"},
            ],
            "absences": [],
        }
        resp = await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=replace",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

        # Verify old data is gone, new data is present
        export = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        export_data = export.json()
        assert len(export_data["entries"]) == 1
        assert export_data["entries"][0]["description"] == "replaced"
        assert len(export_data["absences"]) == 0

    async def test_leader_imports_for_dept_member(
        self, client: AsyncClient, admin_token: str, leader_token: str, department: dict,
    ):
        """Leader can import data for users in their department."""
        user_data, token = await _create_dept_worker(client, admin_token, department)

        payload = {
            "entries": [
                {"date": "2024-07-01", "start_time": "08:00:00", "end_time": "16:00:00",
                 "break_minutes": 30, "description": "leader-imported"},
            ],
            "absences": [],
        }
        resp = await client.post(
            f"/api/v1/data/import/{user_data['id']}?mode=merge",
            json=payload,
            headers=auth_header(leader_token),
        )
        assert resp.status_code == 200
        assert resp.json()["entries_imported"] == 1

    async def test_leader_cannot_import_outside_dept(
        self, client: AsyncClient, leader_token: str, worker_user: dict,
    ):
        """Leader cannot import data for users outside their department."""
        payload = {"entries": [], "absences": []}
        resp = await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=merge",
            json=payload,
            headers=auth_header(leader_token),
        )
        assert resp.status_code == 403

    async def test_worker_cannot_import_for_others(
        self, client: AsyncClient, worker_token: str, admin_user,
    ):
        """Workers cannot use the import-for-user endpoint."""
        payload = {"entries": [], "absences": []}
        resp = await client.post(
            f"/api/v1/data/import/{admin_user.id}?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_import_nonexistent_user(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        payload = {"entries": [], "absences": []}
        resp = await client.post(
            f"/api/v1/data/import/{fake_id}?mode=merge",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    async def test_import_invalid_mode_for_user(
        self, client: AsyncClient, admin_token: str, worker_user: dict,
    ):
        payload = {"entries": [], "absences": []}
        resp = await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=bogus",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400


# ── Export → Import round-trip for another user ──────────────────────

class TestCrossUserRoundTrip:
    async def test_admin_roundtrip_export_import(
        self, client: AsyncClient, admin_token: str, worker_user: dict, worker_token: str,
    ):
        """Export a user's data and re-import it (admin acting on behalf of worker)."""
        # Create data for the worker
        await create_entry(client, worker_token, entry_date="2024-11-01", description="rt1")
        await create_absence(client, worker_token, absence_date="2024-11-10")

        # Admin exports worker data
        export_resp = await client.get(
            f"/api/v1/data/export/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert export_resp.status_code == 200
        exported = export_resp.json()

        # Admin replaces worker data with empty
        await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=replace",
            json={"entries": [], "absences": []},
            headers=auth_header(admin_token),
        )

        # Verify empty
        check = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        assert len(check.json()["entries"]) == 0

        # Re-import
        import_resp = await client.post(
            f"/api/v1/data/import/{worker_user['id']}?mode=merge",
            json={"entries": exported["entries"], "absences": exported["absences"]},
            headers=auth_header(admin_token),
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["entries_imported"] == 1
        assert import_resp.json()["absences_imported"] == 1


# ── Default schedule on user creation ────────────────────────────────

class TestDefaultScheduleOnCreation:
    async def test_new_user_has_default_schedule(
        self, client: AsyncClient, admin_token: str,
    ):
        """Every newly created user gets a Mon-Fri 480min default schedule."""
        resp = await client.post(
            "/api/v1/users",
            json={
                "email": "newuser@test.com",
                "password": "Newuser123!",
                "first_name": "New",
                "last_name": "User",
                "role": "worker",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201

        # Login and check schedule
        login = await client.post("/api/v1/auth/login", json={
            "email": "newuser@test.com",
            "password": "Newuser123!",
        })
        token = login.json()["access_token"]

        sched = await client.get("/api/v1/schedule", headers=auth_header(token))
        assert sched.status_code == 200
        data = sched.json()
        assert data["monday_minutes"] == 480
        assert data["tuesday_minutes"] == 480
        assert data["wednesday_minutes"] == 480
        assert data["thursday_minutes"] == 480
        assert data["friday_minutes"] == 480
        assert data["saturday_minutes"] == 0
        assert data["sunday_minutes"] == 0

    async def test_default_schedule_valid_from_2020(
        self, client: AsyncClient, worker_token: str,
    ):
        """Default schedule valid_from is 2020-01-01."""
        resp = await client.get("/api/v1/schedule", headers=auth_header(worker_token))
        data = resp.json()
        assert data["valid_from"] == "2020-01-01"

    async def test_worker_default_schedule_roundtrip(
        self, client: AsyncClient, worker_token: str,
    ):
        """Worker with default schedule can override it."""
        # Override
        resp = await client.post("/api/v1/schedule", json={
            "valid_from": "2024-06-01",
            "monday_minutes": 360,
            "tuesday_minutes": 360,
            "wednesday_minutes": 360,
            "thursday_minutes": 360,
            "friday_minutes": 360,
            "saturday_minutes": 0,
            "sunday_minutes": 0,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 201

        # Verify the new schedule is returned
        sched = await client.get("/api/v1/schedule", headers=auth_header(worker_token))
        data = sched.json()
        assert data["monday_minutes"] == 360
