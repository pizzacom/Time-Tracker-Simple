"""Report schemas."""
import uuid
from datetime import date
from typing import Optional, List

from pydantic import BaseModel


class DayReport(BaseModel):
    date: date
    weekday: str
    soll_minutes: int
    ist_minutes: int
    delta_minutes: int
    entry_count: int
    is_holiday: bool = False
    is_absence: bool = False
    absence_type: Optional[str] = None
    overtime_used_minutes: int = 0
    entries: List[dict] = []


class MonthlyReport(BaseModel):
    user_id: uuid.UUID
    user_name: str
    year: int
    month: int
    soll_total: int
    ist_total: int
    delta_total: int
    overtime_earned: int
    overtime_used: int
    overtime_balance: int
    work_days: int
    vacation_days: int
    sick_days: int
    holiday_count: int
    days: List[DayReport]


class DepartmentOverviewEntry(BaseModel):
    user_id: uuid.UUID
    user_name: str
    soll_total: int
    ist_total: int
    delta_total: int
    overtime_balance: int
    vacation_days_remaining: int


class DepartmentOverview(BaseModel):
    department_id: uuid.UUID
    department_name: str
    year: int
    month: int
    members: List[DepartmentOverviewEntry]


class SystemSummary(BaseModel):
    total_users: int
    total_departments: int
    total_entries: int
    current_month_ist: int
    current_month_soll: int
    total_overtime_balance: int
