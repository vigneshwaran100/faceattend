from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import Mock

import pytest

from app.models.attendance import Attendance
from app.models.attendance_summary import AttendanceSummary
from app.models.employee import Employee
from app.services.attendance_service import AttendanceService


def create_service() -> tuple[
    AttendanceService,
    Mock,
]:
    repository = Mock()

    service = AttendanceService(
        repository=repository,
    )

    return service, repository


def create_attendance(
    *,
    check_in: datetime,
    check_out: datetime | None = None,
    status: str = "in_progress",
) -> Attendance:
    return Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=check_in.date(),
        check_in=check_in.time(),
        check_out=(
            check_out.time()
            if check_out is not None
            else None
        ),
        status=status,
        created_at=check_in,
        updated_at=check_out or check_in,
    )


def test_check_in_creates_attendance() -> None:
    service, repository = create_service()

    now = datetime(
        2026,
        8,
        18,
        9,
        30,
        tzinfo=timezone.utc,
    )

    repository.get_by_employee_and_date.return_value = None

    repository.create.side_effect = lambda attendance: attendance

    result = service.check_in(
        "EMP001",
        now=now,
    )

    assert result.employee_id == "EMP001"
    assert result.check_in == now.time()
    assert result.check_out is None
    assert result.status == "in_progress"

    repository.create.assert_called_once()


def test_check_in_does_not_overwrite_first_check_in() -> None:
    service, repository = create_service()

    first_check_in = datetime(
        2026,
        8,
        18,
        9,
        30,
        tzinfo=timezone.utc,
    )

    second_scan = datetime(
        2026,
        8,
        18,
        10,
        30,
        tzinfo=timezone.utc,
    )

    existing = create_attendance(
        check_in=first_check_in,
    )

    repository.get_by_employee_and_date.return_value = (
        existing
    )

    result = service.check_in(
        "EMP001",
        now=second_scan,
    )

    assert result == existing
    assert result.check_in == first_check_in.time()

    repository.create.assert_not_called()


def test_check_out_updates_checkout_time_and_keeps_in_progress() -> None:
    service, repository = create_service()

    check_in_time = datetime(
        2026,
        8,
        18,
        9,
        0,
        tzinfo=timezone.utc,
    )

    check_out_time = check_in_time + timedelta(
        hours=8,
    )

    existing = create_attendance(
        check_in=check_in_time,
    )

    repository.get_by_employee_and_date.return_value = (
        existing
    )

    repository.update.side_effect = lambda attendance: (
        attendance
    )

    result = service.check_out(
        "EMP001",
        now=check_out_time,
    )

    assert result.check_in == check_in_time.time()
    assert result.check_out == check_out_time.time()
    assert result.status == "in_progress"

    repository.update.assert_called_once()


def test_latest_checkout_overwrites_previous_checkout() -> None:
    service, repository = create_service()

    check_in_time = datetime(
        2026,
        8,
        18,
        9,
        0,
        tzinfo=timezone.utc,
    )

    previous_check_out = check_in_time + timedelta(
        hours=8,
    )

    latest_check_out = check_in_time + timedelta(
        hours=9,
    )

    existing = create_attendance(
        check_in=check_in_time,
        check_out=previous_check_out,
        status="in_progress",
    )

    repository.get_by_employee_and_date.return_value = (
        existing
    )

    repository.update.side_effect = lambda attendance: (
        attendance
    )

    result = service.check_out(
        "EMP001",
        now=latest_check_out,
    )

    assert result.check_in == check_in_time.time()
    assert result.check_out == latest_check_out.time()
    assert result.status == "in_progress"

    repository.update.assert_called_once()


def test_check_out_rejects_missing_attendance() -> None:
    service, repository = create_service()

    repository.get_by_employee_and_date.return_value = None

    now = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError,
        match="No attendance record",
    ):
        service.check_out(
            "EMP001",
            now=now,
        )

    repository.update.assert_not_called()


def test_check_out_rejects_missing_check_in() -> None:
    service, repository = create_service()

    now = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=timezone.utc,
    )

    existing = Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=now.date(),
        check_in=None,
        check_out=None,
        status="in_progress",
        created_at=now,
        updated_at=now,
    )

    repository.get_by_employee_and_date.return_value = (
        existing
    )

    with pytest.raises(
        ValueError,
        match="Check-in time missing",
    ):
        service.check_out(
            "EMP001",
            now=now,
        )

    repository.update.assert_not_called()


def test_calculate_working_hours() -> None:
    service, _ = create_service()

    check_in = datetime(
        2026,
        8,
        18,
        9,
        0,
        tzinfo=timezone.utc,
    ).time()

    check_out = datetime(
        2026,
        8,
        18,
        17,
        30,
        tzinfo=timezone.utc,
    ).time()

    result = service.calculate_working_hours(
        check_in,
        check_out,
    )

    assert result == 8.5


def test_calculate_working_hours_rejects_checkout_before_check_in() -> None:
    service, _ = create_service()

    check_in = datetime(
        2026,
        8,
        18,
        18,
        0,
        tzinfo=timezone.utc,
    ).time()

    check_out = datetime(
        2026,
        8,
        18,
        9,
        0,
        tzinfo=timezone.utc,
    ).time()

    with pytest.raises(
        ValueError,
        match="Check-out cannot be before check-in",
    ):
        service.calculate_working_hours(
            check_in,
            check_out,
        )


def test_finalize_attendance_with_full_hours_marks_present() -> None:
    service, repository = create_service()

    check_in = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2026, 8, 18, 18, 0, tzinfo=timezone.utc)

    existing = create_attendance(
        check_in=check_in,
        check_out=check_out,
        status="in_progress",
    )
    repository.get_by_employee_and_date.return_value = existing
    repository.update.side_effect = lambda attendance: attendance

    result = service.finalize_attendance("EMP001", check_in.date())

    assert result.status == "present"
    repository.update.assert_called_once()


def test_finalize_attendance_with_less_hours_marks_half_day() -> None:
    service, repository = create_service()

    check_in = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2026, 8, 18, 14, 0, tzinfo=timezone.utc)

    existing = create_attendance(
        check_in=check_in,
        check_out=check_out,
        status="in_progress",
    )
    repository.get_by_employee_and_date.return_value = existing
    repository.update.side_effect = lambda attendance: attendance

    result = service.finalize_attendance("EMP001", check_in.date())

    assert result.status == "half_day"


def test_finalize_attendance_without_checkout_marks_incomplete() -> None:
    service, repository = create_service()

    check_in = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)

    existing = create_attendance(
        check_in=check_in,
        check_out=None,
        status="in_progress",
    )
    repository.get_by_employee_and_date.return_value = existing
    repository.update.side_effect = lambda attendance: attendance

    result = service.finalize_attendance("EMP001", check_in.date())

    assert result.status == "incomplete"


def test_finalize_attendance_rejects_missing_record() -> None:
    service, repository = create_service()
    repository.get_by_employee_and_date.return_value = None

    with pytest.raises(ValueError, match="No attendance found"):
        service.finalize_attendance("EMP001", datetime(2026, 8, 18).date())


def test_finalize_day() -> None:
    service, repository = create_service()

    check_in = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)
    check_out = datetime(2026, 8, 18, 18, 0, tzinfo=timezone.utc)

    rec1 = create_attendance(
        check_in=check_in,
        check_out=check_out,
        status="in_progress",
    )
    repository.get_all_by_date.return_value = [rec1]
    repository.get_by_employee_and_date.return_value = rec1
    repository.update.side_effect = lambda attendance: attendance

    results = service.finalize_day(check_in.date())

    assert len(results) == 1
    assert results[0].status == "present"


def test_get_attendance_history_returns_records() -> None:
    service, repository = create_service()

    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 23),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    repository.get_all_by_employee.return_value = records

    result = service.get_attendance_history("EMP001")

    assert result == records
    repository.get_all_by_employee.assert_called_once_with("EMP001")


def test_get_attendance_history_returns_empty_list() -> None:
    service, repository = create_service()
    repository.get_all_by_employee.return_value = []

    result = service.get_attendance_history("EMP999")

    assert result == []
    repository.get_all_by_employee.assert_called_once_with("EMP999")


    from app.services.attendance_service import AttendanceService


def test_get_attendance_history_by_date_range() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    service.get_attendance_history_by_date_range(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    repository.get_by_employee_and_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

def test_get_attendance_summary_calculates_correct_values() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 1),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Attendance(
            attendance_id="ATT002",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 2),
            check_in=time(9, 0),
            check_out=time(13, 0),
            status="half_day",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Attendance(
            attendance_id="ATT003",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 3),
            check_in=time(9, 0),
            check_out=None,
            status="in_progress",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    repository.get_by_employee_and_date_range.return_value = records

    result = service.get_attendance_summary(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert result.employee_id == "EMP001"
    assert result.start_date == date(2026, 8, 1)
    assert result.end_date == date(2026, 8, 31)
    assert result.total_records == 3
    assert result.total_working_days == 3
    assert result.present_days == 1
    assert result.half_days == 1
    assert result.in_progress_days == 1
    assert result.total_working_hours == 13.0
    assert result.attendance_percentage == 50.0

    repository.get_by_employee_and_date_range.assert_called_once_with(
        "EMP001",
        date(2026, 8, 1),
        date(2026, 8, 31),
    )

def test_get_attendance_summary_returns_zero_for_no_records() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    repository.get_by_employee_and_date_range.return_value = []

    result = service.get_attendance_summary(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert result.employee_id == "EMP001"
    assert result.total_records == 0
    assert result.present_days == 0
    assert result.half_days == 0
    assert result.in_progress_days == 0
    assert result.total_working_hours == 0

    repository.get_by_employee_and_date_range.assert_called_once_with(
        "EMP001",
        date(2026, 8, 1),
        date(2026, 8, 31),
    )

def test_get_attendance_summary_excludes_records_without_checkout() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 1),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Attendance(
            attendance_id="ATT002",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 2),
            check_in=time(9, 0),
            check_out=None,
            status="in_progress",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    repository.get_by_employee_and_date_range.return_value = records

    result = service.get_attendance_summary(
        employee_id="EMP001",
    )

    assert result.total_records == 2
    assert result.in_progress_days == 1
    assert result.total_working_hours == 9.0


def test_process_end_of_day() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    target_date = date(2026, 8, 29)
    now = datetime(2026, 8, 29, 18, 0)

    # In-progress employee who checked in & out for 9h
    emp1_rec = Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=target_date,
        check_in=time(9, 0),
        check_out=time(18, 0),
        status="in_progress",
        created_at=now,
        updated_at=now,
    )

    # Active employees: EMP001 and EMP002 (EMP002 has no attendance)
    active_employees = [
        Employee(
            employee_id="EMP001",
            name="Vigneshwaran",
            email="vignesh@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="AI Engineer",
            status="active",
            created_at=now,
            updated_at=now,
        ),
        Employee(
            employee_id="EMP002",
            name="John Doe",
            email="john@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="Developer",
            status="active",
            created_at=now,
            updated_at=now,
        ),
    ]

    repository.get_all_by_date.side_effect = [
        [emp1_rec],  # First call inside finalize_day
        [
            Attendance(
                attendance_id="ATT001",
                employee_id="EMP001",
                attendance_date=target_date,
                check_in=time(9, 0),
                check_out=time(18, 0),
                status="present",
                created_at=now,
                updated_at=now,
            ),
            Attendance(
                attendance_id="ATT002",
                employee_id="EMP002",
                attendance_date=target_date,
                check_in=None,
                check_out=None,
                status="absent",
                created_at=now,
                updated_at=now,
            ),
        ],  # Second call to compute final counts
    ]

    # For finalize_attendance and mark_absent
    def mock_get_by_emp_and_date(emp_id: str, d: date) -> Attendance | None:
        if emp_id == "EMP001":
            return emp1_rec
        return None

    repository.get_by_employee_and_date.side_effect = mock_get_by_emp_and_date
    repository.update.side_effect = lambda a: a
    repository.create.side_effect = lambda a: a

    summary = service.process_end_of_day(
        active_employees=active_employees,
        attendance_date=target_date,
        now=now,
    )

    assert summary.attendance_date == target_date
    assert summary.present == 1
    assert summary.absent == 1
    assert summary.half_day == 0
    assert summary.incomplete == 0
    assert summary.total_processed == 2


def test_get_daily_attendance_report() -> None:
    repository = Mock()
    service = AttendanceService(repository)

    target_date = date(2026, 8, 29)
    now = datetime(2026, 8, 29, 18, 0)

    active_employees = [
        Employee(
            employee_id="EMP001",
            name="Vigneshwaran",
            email="vignesh@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="AI Engineer",
            status="active",
            created_at=now,
            updated_at=now,
        ),
        Employee(
            employee_id="EMP002",
            name="John Doe",
            email="john@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="Developer",
            status="active",
            created_at=now,
            updated_at=now,
        ),
    ]

    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id="EMP001",
            attendance_date=target_date,
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=now,
            updated_at=now,
        )
    ]
    repository.get_all_by_date.return_value = records

    report = service.get_daily_attendance_report(
        active_employees=active_employees,
        attendance_date=target_date,
    )

    assert report.attendance_date == target_date
    assert report.total_employees == 2
    assert len(report.records) == 2

    emp1_item = report.records[0]
    assert emp1_item.employee_id == "EMP001"
    assert emp1_item.name == "Vigneshwaran"
    assert emp1_item.check_in == time(9, 0)
    assert emp1_item.check_out == time(18, 0)
    assert emp1_item.working_hours == 9.0
    assert emp1_item.status == "present"

    emp2_item = report.records[1]
    assert emp2_item.employee_id == "EMP002"
    assert emp2_item.name == "John Doe"
    assert emp2_item.check_in is None
    assert emp2_item.check_out is None
    assert emp2_item.working_hours is None
    assert emp2_item.status == "absent"


def test_mark_absent_preserves_concurrent_check_in() -> None:
    service, repository = create_service()
    now = datetime(2026, 8, 29, 22, 0, 0)
    target_date = date(2026, 8, 29)

    employee = Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="vignesh@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="AI Engineer",
        status="active",
        created_at=now,
        updated_at=now,
    )

    # Initial check: no record found
    repository.get_by_employee_and_date.return_value = None

    # When create is called during mark_absent, repository resolves race and returns the concurrent check-in
    concurrent_check_in_record = Attendance(
        attendance_id="ATT_CONCURRENT",
        employee_id="EMP001",
        attendance_date=target_date,
        check_in=time(17, 30),
        check_out=None,
        status="in_progress",
        created_at=now,
        updated_at=now,
    )
    repository.create.return_value = concurrent_check_in_record

    result = service.mark_absent(
        employee_id="EMP001",
        attendance_date=target_date,
        now=now,
    )

    # The concurrent check-in is preserved and returned
    assert result.attendance_id == "ATT_CONCURRENT"
    assert result.check_in == time(17, 30)
    assert result.status == "in_progress"



    