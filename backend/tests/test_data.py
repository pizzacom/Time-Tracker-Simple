"""Tests for /api/v1/data endpoints (personal data export/import)."""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_entry(client, token, date="2024-06-15", start="08:00", end="16:30", brk=30, desc="work"):
    resp = await client.post(
        "/api/v1/entries",
        json={
            "date": date,
            "start_time": start,
            "end_time": end,
            "break_minutes": brk,
            "description": desc,
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_absence(client, token, date="2024-06-20", atype="urlaub", note=None):
    resp = await client.post(
        "/api/v1/absences",
        json={"date": date, "type": atype, "note": note},
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Export ─────────────────────────────────────────────────────────

class TestExportPersonalData:
    async def test_export_empty(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == 1
        assert data["entries"] == []
        assert data["absences"] == []
        assert data["overtime"] == []
        assert "user" in data

    async def test_export_with_entries(self, client: AsyncClient, worker_token):
        await _create_entry(client, worker_token)
        resp = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        data = resp.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["date"] == "2024-06-15"
        assert data["entries"][0]["description"] == "work"

    async def test_export_with_absences(self, client: AsyncClient, worker_token):
        await _create_absence(client, worker_token)
        resp = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        data = resp.json()
        assert len(data["absences"]) == 1
        assert data["absences"][0]["type"] == "urlaub"

    async def test_export_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/data/export")
        assert resp.status_code == 401


# ── Import (merge mode) ───────────────────────────────────────────

class TestImportMerge:
    async def test_import_entries(self, client: AsyncClient, worker_token):
        payload = {
            "entries": [
                {"date": "2024-07-01", "start_time": "08:00:00", "end_time": "16:00:00", "break_minutes": 30, "description": "imported"},
            ],
            "absences": [],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries_imported"] == 1
        assert data["entries_skipped"] == 0

        # Verify it was actually created
        entries = await client.get(
            "/api/v1/entries?date_from=2024-07-01&date_to=2024-07-01",
            headers=auth_header(worker_token),
        )
        assert len(entries.json()) == 1

    async def test_merge_skips_duplicates(self, client: AsyncClient, worker_token):
        await _create_entry(client, worker_token, date="2024-07-02", start="09:00", end="17:00")

        payload = {
            "entries": [
                {"date": "2024-07-02", "start_time": "09:00:00", "end_time": "17:00:00", "break_minutes": 0, "description": "dup"},
            ],
            "absences": [],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        data = resp.json()
        assert data["entries_skipped"] == 1
        assert data["entries_imported"] == 0

    async def test_import_absences(self, client: AsyncClient, worker_token):
        payload = {
            "entries": [],
            "absences": [
                {"date": "2024-08-01", "type": "krank", "note": "flu"},
            ],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        data = resp.json()
        assert data["absences_imported"] == 1

    async def test_merge_skips_duplicate_absences(self, client: AsyncClient, worker_token):
        await _create_absence(client, worker_token, date="2024-08-02", atype="krank")
        payload = {
            "entries": [],
            "absences": [
                {"date": "2024-08-02", "type": "krank"},
            ],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        data = resp.json()
        assert data["absences_skipped"] == 1


# ── Import (replace mode) ─────────────────────────────────────────

class TestImportReplace:
    async def test_replace_clears_existing(self, client: AsyncClient, worker_token):
        # Create existing entry
        await _create_entry(client, worker_token, date="2024-06-10")
        await _create_absence(client, worker_token, date="2024-06-11")

        # Import with replace
        payload = {
            "entries": [
                {"date": "2024-09-01", "start_time": "08:00:00", "end_time": "12:00:00", "break_minutes": 0, "description": "new"},
            ],
            "absences": [],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=replace",
            json=payload,
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["entries_imported"] == 1

        # Original entry should be gone
        entries = await client.get(
            "/api/v1/entries?date_from=2024-06-10&date_to=2024-06-10",
            headers=auth_header(worker_token),
        )
        assert len(entries.json()) == 0


# ── Validation ─────────────────────────────────────────────────────

class TestImportValidation:
    async def test_invalid_mode(self, client: AsyncClient, worker_token):
        resp = await client.post(
            "/api/v1/data/import?mode=invalid",
            json={"entries": [], "absences": []},
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 400

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json={"entries": [], "absences": []},
        )
        assert resp.status_code == 401

    async def test_skips_invalid_entries(self, client: AsyncClient, worker_token):
        """Entries with end <= start should be skipped."""
        payload = {
            "entries": [
                {"date": "2024-07-05", "start_time": "17:00:00", "end_time": "08:00:00", "break_minutes": 0},
            ],
            "absences": [],
        }
        resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json=payload,
            headers=auth_header(worker_token),
        )
        data = resp.json()
        assert data["entries_skipped"] == 1
        assert data["entries_imported"] == 0


# ── Round-trip test (export → import) ──────────────────────────────

class TestRoundTrip:
    async def test_export_then_import(self, client: AsyncClient, worker_token):
        """Data exported and re-imported should round-trip correctly."""
        # Create data
        await _create_entry(client, worker_token, date="2024-10-01", start="08:00", end="16:30", desc="roundtrip")
        await _create_absence(client, worker_token, date="2024-10-05", atype="urlaub")

        # Export
        export_resp = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        exported = export_resp.json()
        assert len(exported["entries"]) == 1
        assert len(exported["absences"]) == 1

        # Delete existing (replace mode with empty)
        await client.post(
            "/api/v1/data/import?mode=replace",
            json={"entries": [], "absences": []},
            headers=auth_header(worker_token),
        )

        # Verify empty
        check = await client.get("/api/v1/data/export", headers=auth_header(worker_token))
        assert len(check.json()["entries"]) == 0

        # Re-import
        import_resp = await client.post(
            "/api/v1/data/import?mode=merge",
            json={"entries": exported["entries"], "absences": exported["absences"]},
            headers=auth_header(worker_token),
        )
        assert import_resp.json()["entries_imported"] == 1
        assert import_resp.json()["absences_imported"] == 1
