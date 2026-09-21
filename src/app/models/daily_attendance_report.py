from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class DailyAttendanceItem:
    employee_id: str
    name: str
    check_in: time | None
    check_out: time | None
    working_hours: float | None
    status: str


@dataclass(frozen=True)
class DailyAttendanceReport:
    attendance_date: date
    total_employees: int
    records: list[DailyAttendanceItem]
