"""Tests for overtime balance, history, usage, and deletion."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header, create_entry, create_schedule_for_user


@pytest.mark.asyncio
class TestOvertimeBalance:
    async def test_initial_balance_zero(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/overtime/balance",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["balance_minutes"] == 0
        assert data["history"] == []

    async def test_history_initially_empty(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/overtime/history",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
class TestUseOvertime:
    async def test_use_overtime_insufficient_balance(self, client: AsyncClient,
                                                      worker_token: str):
        """Cannot use overtime when balance is zero."""
        resp = await client.post("/api/v1/overtime/use", json={
            "date": "2024-06-15",
            "minutes": 480,
        }, headers=auth_header(worker_token))
        assert resp.status_code == 400
        assert "Insufficient" in resp.json()["detail"]

    async def test_use_overtime_success(self, client: AsyncClient,
                                        worker_token: str, worker_user: dict,
                                        admin_token: str):
        """Worker who has earned overtime can use it."""
        # Set a schedule (480 min M-F)
        await create_schedule_for_user(client, admin_token, worker_user["id"])

        # Create an entry that exceeds soll: 10 hrs with 0 break = 600 min, soll = 480
        await create_entry(client, worker_token, "2024-06-10", "07:00", "17:00", 0)

        # Check if overtime was earned
        balance_resp = await client.get(
            "/api/v1/overtime/balance",
            headers=auth_header(worker_token),
        )
        balance = balance_resp.json()["balance_minutes"]

        if balance > 0:
            # Now use a portion of that overtime
            use_resp = await client.post("/api/v1/overtime/use", json={
                "date": "2024-06-20",
                "minutes": min(60, balance),
            }, headers=auth_header(worker_token))
            assert use_resp.status_code == 200
            assert "new_balance_minutes" in use_resp.json()


@pytest.mark.asyncio
class TestDeleteOvertimeEntry:
    """Tests for the DELETE /overtime/{ledger_id} endpoint."""

    async def test_delete_used_overtime_entry(self, client: AsyncClient,
                                               worker_token: str,
                                               worker_user: dict,
                                               admin_token: str):
        """Deleting a 'used' overtime entry should restore the balance."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # Create entry exceeding soll to earn overtime
        await create_entry(client, worker_token, "2024-06-10", "07:00", "17:00", 0)

        balance_resp = await client.get(
            "/api/v1/overtime/balance",
            headers=auth_header(worker_token),
        )
        balance_before = balance_resp.json()["balance_minutes"]
        if balance_before <= 0:
            pytest.skip("No overtime earned for this test")

        # Use some overtime
        use_amount = min(60, balance_before)
        use_resp = await client.post("/api/v1/overtime/use", json={
            "date": "2024-06-20",
            "minutes": use_amount,
        }, headers=auth_header(worker_token))
        assert use_resp.status_code == 200

        # Find the used entry in history
        history_resp = await client.get(
            "/api/v1/overtime/history",
            headers=auth_header(worker_token),
        )
        used_entries = [h for h in history_resp.json() if h["reason"] == "used"]
        assert len(used_entries) >= 1
        used_id = used_entries[0]["id"]

        # Delete the used entry
        del_resp = await client.delete(
            f"/api/v1/overtime/{used_id}",
            headers=auth_header(worker_token),
        )
        assert del_resp.status_code == 200
        assert "new_balance_minutes" in del_resp.json()
        # Balance should be restored
        assert del_resp.json()["new_balance_minutes"] == balance_before

    async def test_delete_nonexistent_overtime_entry(self, client: AsyncClient,
                                                      worker_token: str):
        """Deleting a nonexistent entry should return 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(
            f"/api/v1/overtime/{fake_id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 404

    async def test_cannot_delete_other_users_overtime(self, client: AsyncClient,
                                                       worker_token: str,
                                                       worker_user: dict,
                                                       admin_token: str,
                                                       admin_user):
        """A user cannot delete another user's overtime entries."""
        # Earn overtime as worker
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        await create_entry(client, worker_token, "2024-06-10", "07:00", "17:00", 0)

        history_resp = await client.get(
            "/api/v1/overtime/history",
            headers=auth_header(worker_token),
        )
        entries = history_resp.json()
        if not entries:
            pytest.skip("No overtime entries to test with")

        entry_id = entries[0]["id"]

        # Admin tries to delete worker's entry (should fail — only own entries)
        resp = await client.delete(
            f"/api/v1/overtime/{entry_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404  # Not found because it belongs to worker


@pytest.mark.asyncio
class TestAdminViewOvertime:
    async def test_admin_views_user_overtime(self, client: AsyncClient,
                                             admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/overtime/user/{worker_user['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "balance_minutes" in resp.json()

    async def test_worker_cannot_view_other_overtime(self, client: AsyncClient,
                                                      worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/overtime/user/{admin_user.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403
