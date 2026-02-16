"""Schema validation tests — ensure Pydantic models accept/reject correctly."""
import pytest
from datetime import date, time
from pydantic import ValidationError

from app.schemas.entry import EntryCreate, EntryUpdate, EntryResponse
from app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate
from app.schemas.schedule import WorkScheduleCreate
from app.schemas.absence import AbsenceCreate
from app.schemas.holiday import HolidayCreate
from app.schemas.department import DepartmentCreate
from app.schemas.overtime import OvertimeUseRequest


class TestEntrySchemas:
    def test_entry_create_valid(self):
        e = EntryCreate(date="2024-06-10", start_time="08:00", end_time="17:00",
                        break_minutes=60)
        assert e.date == date(2024, 6, 10)
        assert e.start_time == time(8, 0)
        assert e.break_minutes == 60

    def test_entry_create_missing_date(self):
        with pytest.raises(ValidationError):
            EntryCreate(start_time="08:00", end_time="17:00")

    def test_entry_create_negative_break(self):
        with pytest.raises(ValidationError):
            EntryCreate(date="2024-06-10", start_time="08:00", end_time="17:00",
                        break_minutes=-10)

    def test_entry_update_all_none(self):
        """All fields are optional — empty update is valid."""
        u = EntryUpdate()
        assert u.date is None
        assert u.start_time is None

    def test_entry_update_coerces_empty_string(self):
        """EntryUpdate model_validator converts '' to None."""
        u = EntryUpdate(date="", start_time="", end_time="", description="")
        assert u.date is None
        assert u.start_time is None
        assert u.description is None

    def test_entry_update_valid_partial(self):
        u = EntryUpdate(start_time="09:00")
        assert u.start_time == time(9, 0)
        assert u.date is None


class TestUserSchemas:
    def test_user_create_valid(self):
        u = UserCreate(email="a@b.com", first_name="A", last_name="B",
                       password="123456")
        assert u.email == "a@b.com"
        assert u.role == "worker"

    def test_user_create_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="a@b.com", first_name="A", last_name="B",
                       password="12")

    def test_user_update_partial(self):
        u = UserUpdate(first_name="New")
        assert u.first_name == "New"
        assert u.role is None

    def test_user_profile_update(self):
        u = UserProfileUpdate(first_name="X", last_name="Y")
        assert u.first_name == "X"


class TestScheduleSchemas:
    def test_schedule_create_default(self):
        s = WorkScheduleCreate(valid_from="2024-01-01")
        assert s.monday_minutes == 480
        assert s.saturday_minutes == 0

    def test_schedule_create_custom(self):
        s = WorkScheduleCreate(
            valid_from="2024-01-01",
            monday_minutes=0, tuesday_minutes=0, wednesday_minutes=0,
            thursday_minutes=0, friday_minutes=0,
            saturday_minutes=240, sunday_minutes=240,
        )
        assert s.saturday_minutes == 240

    def test_schedule_create_out_of_range(self):
        with pytest.raises(ValidationError):
            WorkScheduleCreate(valid_from="2024-01-01", monday_minutes=2000)


class TestAbsenceSchemas:
    def test_absence_create_valid(self):
        a = AbsenceCreate(date="2024-06-14", type="urlaub")
        assert a.type == "urlaub"

    def test_absence_create_invalid_type(self):
        with pytest.raises(ValidationError):
            AbsenceCreate(date="2024-06-14", type="party")


class TestHolidaySchemas:
    def test_holiday_create_valid(self):
        h = HolidayCreate(date="2024-12-25", name="Weihnachten")
        assert h.is_half_day is False

    def test_holiday_create_half_day(self):
        h = HolidayCreate(date="2024-12-24", name="Heiligabend", is_half_day=True)
        assert h.is_half_day is True


class TestDepartmentSchemas:
    def test_department_create_valid(self):
        d = DepartmentCreate(name="Engineering")
        assert d.name == "Engineering"


class TestOvertimeSchemas:
    def test_overtime_use_valid(self):
        o = OvertimeUseRequest(date="2024-06-15", minutes=60)
        assert o.minutes == 60

    def test_overtime_use_zero_minutes(self):
        with pytest.raises(ValidationError):
            OvertimeUseRequest(date="2024-06-15", minutes=0)

    def test_overtime_use_negative_minutes(self):
        with pytest.raises(ValidationError):
            OvertimeUseRequest(date="2024-06-15", minutes=-30)
