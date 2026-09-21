from datetime import date, datetime, time, timezone

from app.models.attendance import Attendance


def test_attendance_creation() -> None:
    now = datetime.now(timezone.utc)

    attendance = Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=date(2026, 8, 17),
        check_in=time(9, 0),
        check_out=None,
        status="present",
        created_at=now,
        updated_at=now,
    )

    assert attendance.employee_id == "EMP001"
    assert attendance.status == "present"
    assert attendance.check_in == time(9, 0)