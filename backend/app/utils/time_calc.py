"""Time calculation utilities."""
from datetime import time, date, timedelta
from typing import List, Optional


def time_to_minutes(t: time) -> int:
    """Convert a time object to minutes since midnight."""
    return t.hour * 60 + t.minute


def minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight to a time object."""
    h = min(minutes // 60, 23)
    m = minutes % 60
    return time(hour=h, minute=m)


def calculate_work_minutes(start_time: time, end_time: time, break_minutes: int) -> int:
    """Calculate net work minutes from start, end and break."""
    start_min = time_to_minutes(start_time)
    end_min = time_to_minutes(end_time)
    gross = end_min - start_min
    return max(0, gross - break_minutes)


def format_duration(minutes: int) -> str:
    """Format minutes as H:MM string."""
    sign = "-" if minutes < 0 else ""
    abs_min = abs(minutes)
    h = abs_min // 60
    m = abs_min % 60
    return f"{sign}{h}:{m:02d}"


def get_weekday_name_de(d: date) -> str:
    """Get German weekday abbreviation."""
    names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    return names[d.weekday()]


def get_weekday_name_en(d: date) -> str:
    """Get English weekday abbreviation."""
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return names[d.weekday()]


def get_month_days(year: int, month: int) -> List[date]:
    """Get all dates in a given month."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    days = []
    current = first_day
    while current <= last_day:
        days.append(current)
        current += timedelta(days=1)
    return days
