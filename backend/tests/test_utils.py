"""Unit tests for utility functions (no DB / no HTTP needed)."""
import pytest
from datetime import date, time

from app.utils.time_calc import (
    time_to_minutes,
    minutes_to_time,
    calculate_work_minutes,
    format_duration,
    get_weekday_name_de,
    get_weekday_name_en,
    get_month_days,
)
from app.utils.password import hash_password, verify_password
from app.utils.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)


# ═══════════════════════════════════════════════════════════════════════
#  time_calc
# ═══════════════════════════════════════════════════════════════════════

class TestTimeToMinutes:
    def test_midnight(self):
        assert time_to_minutes(time(0, 0)) == 0

    def test_noon(self):
        assert time_to_minutes(time(12, 0)) == 720

    def test_with_minutes(self):
        assert time_to_minutes(time(8, 30)) == 510

    def test_end_of_day(self):
        assert time_to_minutes(time(23, 59)) == 1439


class TestMinutesToTime:
    def test_zero(self):
        assert minutes_to_time(0) == time(0, 0)

    def test_normal(self):
        assert minutes_to_time(510) == time(8, 30)

    def test_cap_at_23(self):
        # 1500 min = 25h → capped at 23:xx
        result = minutes_to_time(1500)
        assert result.hour <= 23


class TestCalculateWorkMinutes:
    def test_full_day(self):
        # 08:00 – 17:00, 60 min break = 480 min
        assert calculate_work_minutes(time(8, 0), time(17, 0), 60) == 480

    def test_no_break(self):
        assert calculate_work_minutes(time(9, 0), time(12, 0), 0) == 180

    def test_half_day(self):
        assert calculate_work_minutes(time(8, 0), time(12, 30), 30) == 240

    def test_break_larger_than_work(self):
        # 1h window with 90 min break → capped at 0
        result = calculate_work_minutes(time(8, 0), time(9, 0), 90)
        assert result == 0

    def test_same_start_end(self):
        result = calculate_work_minutes(time(8, 0), time(8, 0), 0)
        assert result == 0


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "0:00"

    def test_positive(self):
        assert format_duration(480) == "8:00"

    def test_with_minutes(self):
        assert format_duration(510) == "8:30"

    def test_negative(self):
        result = format_duration(-120)
        assert "-" in result
        assert "2:00" in result

    def test_small(self):
        assert format_duration(5) == "0:05"


class TestWeekdayNames:
    def test_monday_de(self):
        assert get_weekday_name_de(date(2024, 6, 10)) == "Mo"

    def test_sunday_de(self):
        assert get_weekday_name_de(date(2024, 6, 16)) == "So"

    def test_monday_en(self):
        assert get_weekday_name_en(date(2024, 6, 10)) == "Mon"


class TestGetMonthDays:
    def test_february_2024_leap(self):
        days = get_month_days(2024, 2)
        assert len(days) == 29
        assert days[0] == date(2024, 2, 1)
        assert days[-1] == date(2024, 2, 29)

    def test_february_2025_normal(self):
        days = get_month_days(2025, 2)
        assert len(days) == 28

    def test_january(self):
        days = get_month_days(2024, 1)
        assert len(days) == 31

    def test_april(self):
        days = get_month_days(2024, 4)
        assert len(days) == 30


# ═══════════════════════════════════════════════════════════════════════
#  password
# ═══════════════════════════════════════════════════════════════════════

class TestPassword:
    def test_hash_and_verify(self):
        h = hash_password("MySecret123")
        assert verify_password("MySecret123", h) is True

    def test_wrong_password(self):
        h = hash_password("correct")
        assert verify_password("wrong", h) is False

    def test_hash_is_not_plaintext(self):
        h = hash_password("secret")
        assert h != "secret"


# ═══════════════════════════════════════════════════════════════════════
#  JWT
# ═══════════════════════════════════════════════════════════════════════

class TestJWT:
    def test_access_token_roundtrip(self):
        uid = "d1e2f3a4-b5c6-7d8e-9f00-a1b2c3d4e5f6"
        import uuid
        user_id = uuid.UUID(uid)
        token = create_access_token(user_id, "admin")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == uid
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        import uuid
        user_id = uuid.uuid4()
        token = create_refresh_token(user_id)
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_get_user_id_from_token(self):
        import uuid
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "worker")
        extracted = get_user_id_from_token(token)
        assert extracted == user_id

    def test_decode_invalid_token(self):
        assert decode_token("garbage.token.here") is None

    def test_get_user_id_invalid_token(self):
        assert get_user_id_from_token("bad") is None
