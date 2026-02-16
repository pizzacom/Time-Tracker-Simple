"""Tests for monthly reports, department overview, and system summary."""
import pytest
from httpx import AsyncClient
from tests.conftest import (
    auth_header, create_entry, create_schedule_for_user,
    create_holiday, create_absence,
)


@pytest.mark.asyncio
class TestMyMonthlyReport:
    async def test_empty_month(self, client: AsyncClient, worker_token: str):
        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2024
        assert data["month"] == 6
        assert data["ist_total"] == 0
        assert isinstance(data["days"], list)
        assert len(data["days"]) == 30  # June has 30 days

    async def test_report_with_entry(self, client: AsyncClient,
                                      worker_token: str, worker_user: dict,
                                      admin_token: str):
        # Set schedule so soll is non-zero
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        await create_entry(client, worker_token, "2024-06-10", "08:00", "17:00", 60)

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ist_total"] > 0
        assert data["work_days"] == 1

    async def test_report_defaults_to_current_month(self, client: AsyncClient,
                                                     worker_token: str):
        resp = await client.get(
            "/api/v1/reports/monthly",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200

    async def test_report_soll_calculation(self, client: AsyncClient,
                                            worker_token: str, worker_user: dict,
                                            admin_token: str):
        # Fulltime schedule: 480 min M-F
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        # June 2024 has 20 working days → 480 * 20 = 9600
        assert data["soll_total"] == 9600


@pytest.mark.asyncio
class TestReportAbsenceCrediting:
    """Absences (urlaub/krank) should be credited as Soll hours in reports."""

    async def test_vacation_day_credited_in_report(self, client: AsyncClient,
                                                    worker_token: str,
                                                    worker_user: dict,
                                                    admin_token: str):
        """A vacation day should show soll=480, ist=480, delta=0."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 10, 2024 is a Monday (working day)
        await create_absence(client, worker_token, "2024-06-10", "urlaub")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day10 = next(d for d in data["days"] if d["date"] == "2024-06-10")
        assert day10["is_absence"] is True
        assert day10["absence_type"] == "urlaub"
        assert day10["soll_minutes"] == 480
        assert day10["ist_minutes"] == 480
        assert day10["delta_minutes"] == 0
        assert data["vacation_days"] == 1

    async def test_sick_day_credited_in_report(self, client: AsyncClient,
                                                worker_token: str,
                                                worker_user: dict,
                                                admin_token: str):
        """A sick day should also be credited with soll hours."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 11, 2024 is a Tuesday
        await create_absence(client, worker_token, "2024-06-11", "krank")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day11 = next(d for d in data["days"] if d["date"] == "2024-06-11")
        assert day11["is_absence"] is True
        assert day11["absence_type"] == "krank"
        assert day11["soll_minutes"] == 480
        assert day11["ist_minutes"] == 480
        assert day11["delta_minutes"] == 0
        assert data["sick_days"] == 1

    async def test_absence_on_weekend_no_credit(self, client: AsyncClient,
                                                 worker_token: str,
                                                 worker_user: dict,
                                                 admin_token: str):
        """Absence on a weekend (soll=0) should not add credited hours."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 15, 2024 is a Saturday (soll=0)
        await create_absence(client, worker_token, "2024-06-15", "urlaub")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day15 = next(d for d in data["days"] if d["date"] == "2024-06-15")
        assert day15["soll_minutes"] == 0
        assert day15["ist_minutes"] == 0

    async def test_multiple_absences_credited(self, client: AsyncClient,
                                               worker_token: str,
                                               worker_user: dict,
                                               admin_token: str):
        """Multiple absence days should each be credited."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        await create_absence(client, worker_token, "2024-06-10", "urlaub")
        await create_absence(client, worker_token, "2024-06-11", "krank")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        # Soll should still include all 20 working days (raw soll)
        assert data["soll_total"] == 9600
        # Ist should include 2 * 480 = 960 from credited hours
        assert data["ist_total"] == 960
        assert data["vacation_days"] == 1
        assert data["sick_days"] == 1


@pytest.mark.asyncio
class TestReportHolidayCrediting:
    """Holidays should be credited as Soll hours in reports."""

    async def test_full_day_holiday_credited(self, client: AsyncClient,
                                              worker_token: str,
                                              worker_user: dict,
                                              admin_token: str):
        """A full-day holiday on a weekday should show soll=480, ist=480."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 12, 2024 is a Wednesday
        await create_holiday(client, admin_token, "2024-06-12", "Test Holiday")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day12 = next(d for d in data["days"] if d["date"] == "2024-06-12")
        assert day12["is_holiday"] is True
        assert day12["soll_minutes"] == 480
        assert day12["ist_minutes"] == 480
        assert day12["delta_minutes"] == 0
        assert data["holiday_count"] == 1

    async def test_half_day_holiday_credited(self, client: AsyncClient,
                                              worker_token: str,
                                              worker_user: dict,
                                              admin_token: str):
        """A half-day holiday should credit half the soll."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 13, 2024 is a Thursday
        await create_holiday(client, admin_token, "2024-06-13", "Half Holiday", True)

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day13 = next(d for d in data["days"] if d["date"] == "2024-06-13")
        assert day13["is_holiday"] is True
        assert day13["soll_minutes"] == 240  # 480 / 2
        assert day13["ist_minutes"] == 240
        assert day13["delta_minutes"] == 0

    async def test_holiday_on_weekend_no_credit(self, client: AsyncClient,
                                                 worker_token: str,
                                                 worker_user: dict,
                                                 admin_token: str):
        """Holiday on a weekend (soll=0) should not add credited hours."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # June 16, 2024 is a Sunday
        await create_holiday(client, admin_token, "2024-06-16", "Sunday Holiday")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        day16 = next(d for d in data["days"] if d["date"] == "2024-06-16")
        assert day16["soll_minutes"] == 0
        assert day16["ist_minutes"] == 0

    async def test_holiday_soll_total_unchanged(self, client: AsyncClient,
                                                 worker_token: str,
                                                 worker_user: dict,
                                                 admin_token: str):
        """Soll total should include holiday days at full schedule value."""
        await create_schedule_for_user(client, admin_token, worker_user["id"])
        # 2 weekday holidays in June
        await create_holiday(client, admin_token, "2024-06-10", "Holiday 1")
        await create_holiday(client, admin_token, "2024-06-11", "Holiday 2")

        resp = await client.get(
            "/api/v1/reports/monthly?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        data = resp.json()
        # 20 working days * 480 = 9600 (holidays still count in soll)
        assert data["soll_total"] == 9600


@pytest.mark.asyncio
class TestAdminUserReport:
    async def test_admin_views_user_report(self, client: AsyncClient,
                                           admin_token: str, worker_user: dict):
        resp = await client.get(
            f"/api/v1/reports/monthly/{worker_user['id']}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == worker_user["id"]

    async def test_worker_cannot_view_other_report(self, client: AsyncClient,
                                                    worker_token: str, admin_user):
        resp = await client.get(
            f"/api/v1/reports/monthly/{admin_user.id}?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestDepartmentOverview:
    async def test_admin_gets_dept_overview(self, client: AsyncClient,
                                            admin_token: str, department: dict):
        resp = await client.get(
            f"/api/v1/reports/department/{department['id']}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["department_id"] == department["id"]
        assert isinstance(data["members"], list)

    async def test_worker_cannot_access_dept_overview(self, client: AsyncClient,
                                                      worker_token: str,
                                                      department: dict):
        resp = await client.get(
            f"/api/v1/reports/department/{department['id']}?year=2024&month=6",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403

    async def test_nonexistent_dept(self, client: AsyncClient, admin_token: str):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(
            f"/api/v1/reports/department/{fake_id}?year=2024&month=6",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestSystemSummary:
    async def test_admin_gets_summary(self, client: AsyncClient, admin_token: str):
        resp = await client.get(
            "/api/v1/reports/summary",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_departments" in data
        assert "total_entries" in data

    async def test_worker_cannot_access_summary(self, client: AsyncClient,
                                                 worker_token: str):
        resp = await client.get(
            "/api/v1/reports/summary",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 403
