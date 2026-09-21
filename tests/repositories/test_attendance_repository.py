from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models.attendance import AttendanceORM
from app.database.models.department import DepartmentORM
from app.database.models.employee import EmployeeORM
from app.database.models.team import TeamORM
from app.models.attendance import Attendance
from app.repositories.attendance_repository import (
    AttendanceRepository,
)


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    return Session(engine)


def seed_employee(session: Session) -> None:
    now = datetime.now(timezone.utc)

    session.add(
        TeamORM(
            team_id="TEAM001",
            team_name="AI Team",
            created_at=now,
            updated_at=now,
        )
    )

    session.add(
        DepartmentORM(
            department_id="DEPT001",
            department_name="Engineering",
            created_at=now,
            updated_at=now,
        )
    )

    session.flush()

    session.add(
        EmployeeORM(
            employee_id="EMP001",
            name="Vigneshwaran",
            email="vigneshwaran@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="Software Engineer",
            status="active",
            created_at=now,
            updated_at=now,
        )
    )

    session.flush()


def create_attendance() -> Attendance:
    now = datetime.now(timezone.utc)

    return Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=date(2026, 8, 18),
        check_in=time(9, 30),
        check_out=None,
        status="present",
        created_at=now,
        updated_at=now,
    )


def test_create_attendance() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)

    attendance = create_attendance()

    result = repository.create(attendance)

    assert result.attendance_id == "ATT001"
    assert result.employee_id == "EMP001"
    assert result.status == "present"


def test_get_by_employee_and_date() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)

    attendance = create_attendance()

    repository.create(attendance)

    result = repository.get_by_employee_and_date(
        "EMP001",
        date(2026, 8, 18),
    )

    assert result is not None
    assert result.attendance_id == "ATT001"
    assert result.check_in == time(9, 30)


def test_get_by_employee_and_date_returns_none() -> None:
    session = create_test_session()

    repository = AttendanceRepository(session)

    result = repository.get_by_employee_and_date(
        "EMP001",
        date(2026, 8, 18),
    )

    assert result is None


def test_update_attendance() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)

    attendance = create_attendance()

    repository.create(attendance)

    updated = Attendance(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=date(2026, 8, 18),
        check_in=time(9, 30),
        check_out=time(18, 0),
        status="completed",
        created_at=attendance.created_at,
        updated_at=datetime.now(timezone.utc),
    )

    result = repository.update(updated)

    assert result.check_in == time(9, 30)
    assert result.check_out == time(18, 0)
    assert result.status == "completed"


def test_get_all_by_date() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)

    attendance = create_attendance()
    repository.create(attendance)

    records = repository.get_all_by_date(date(2026, 8, 18))
    assert len(records) == 1
    assert records[0].attendance_id == "ATT001"

    empty_records = repository.get_all_by_date(date(2026, 8, 19))
    assert len(empty_records) == 0


def test_get_all_by_employee_returns_attendance_records() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)
    employee_id = "EMP001"
    now = datetime.now(timezone.utc)

    attendance_1 = Attendance(
        attendance_id="ATT001",
        employee_id=employee_id,
        attendance_date=date(2026, 8, 22),
        check_in=time(9, 0),
        check_out=time(18, 0),
        status="present",
        created_at=now,
        updated_at=now,
    )

    attendance_2 = Attendance(
        attendance_id="ATT002",
        employee_id=employee_id,
        attendance_date=date(2026, 8, 23),
        check_in=time(9, 30),
        check_out=time(18, 30),
        status="present",
        created_at=now,
        updated_at=now,
    )

    repository.create(attendance_1)
    repository.create(attendance_2)

    records = repository.get_all_by_employee(employee_id)

    assert len(records) == 2
    assert records[0].employee_id == employee_id
    assert records[1].employee_id == employee_id

    # Latest attendance should come first
    assert records[0].attendance_date == date(2026, 8, 23)
    assert records[1].attendance_date == date(2026, 8, 22)


def test_get_all_by_employee_returns_empty_list_when_no_records() -> None:
    session = create_test_session()
    repository = AttendanceRepository(session)

    records = repository.get_all_by_employee("EMP999")

    assert records == []


def test_create_attendance_database_error_triggers_rollback() -> None:
    from unittest.mock import Mock
    from sqlalchemy.exc import SQLAlchemyError
    from app.infrastructure.database_error import DatabaseError

    mock_session = Mock()
    mock_session.commit.side_effect = SQLAlchemyError("DB Connection Lost")

    repository = AttendanceRepository(mock_session)
    attendance = create_attendance()

    import pytest
    with pytest.raises(DatabaseError) as exc_info:
        repository.create(attendance)

    assert "Failed to create attendance record" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)
    mock_session.rollback.assert_called_once()


def test_update_attendance_database_error_triggers_rollback() -> None:
    from unittest.mock import Mock
    from sqlalchemy.exc import SQLAlchemyError
    from app.infrastructure.database_error import DatabaseError

    mock_session = Mock()
    mock_session.scalar.return_value = AttendanceORM(
        attendance_id="ATT001",
        employee_id="EMP001",
        attendance_date=date(2026, 8, 18),
        check_in=time(9, 30),
        check_out=None,
        status="in_progress",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_session.commit.side_effect = SQLAlchemyError("DB Commit Failed")

    repository = AttendanceRepository(mock_session)
    attendance = create_attendance()

    import pytest
    with pytest.raises(DatabaseError) as exc_info:
        repository.update(attendance)

    assert "Failed to update attendance record" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)
    mock_session.rollback.assert_called_once()

def test_get_by_employee_and_date_range_returns_records_within_range() -> None:
    session = create_test_session()
    seed_employee(session)

    repository = AttendanceRepository(session)

    employee_id = "EMP001"
    now = datetime.now(timezone.utc)

    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id=employee_id,
            attendance_date=date(2026, 8, 1),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=now,
            updated_at=now,
        ),
        Attendance(
            attendance_id="ATT002",
            employee_id=employee_id,
            attendance_date=date(2026, 8, 15),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=now,
            updated_at=now,
        ),
        Attendance(
            attendance_id="ATT003",
            employee_id=employee_id,
            attendance_date=date(2026, 9, 1),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="present",
            created_at=now,
            updated_at=now,
        ),
    ]

    for attendance in records:
        repository.create(attendance)

    result = repository.get_by_employee_and_date_range(
        employee_id=employee_id,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )

    assert len(result) == 2

    assert result[0].attendance_date == date(2026, 8, 15)
    assert result[1].attendance_date == date(2026, 8, 1)


def test_create_recovers_existing_on_unique_constraint_violation() -> None:
    session = create_test_session()
    seed_employee(session)
    repository = AttendanceRepository(session)

    attendance1 = create_attendance()
    created1 = repository.create(attendance1)
    assert created1.attendance_id == "ATT001"

    # Create a duplicate record for same employee and date (with different ID / check_in)
    now = datetime.now(timezone.utc)
    attendance2 = Attendance(
        attendance_id="ATT002",
        employee_id="EMP001",
        attendance_date=date(2026, 8, 18),
        check_in=time(10, 0),
        check_out=None,
        status="present",
        created_at=now,
        updated_at=now,
    )

    # Must cleanly resolve and return the existing record without crashing
    created2 = repository.create(attendance2)
    assert created2.attendance_id == "ATT001"
    assert created2.check_in == time(9, 30)


def test_create_raises_database_error_on_unrelated_integrity_error() -> None:
    from app.infrastructure.database_error import DatabaseError

    session = create_test_session()
    # Notice: do NOT seed employee, so foreign key / invalid employee occurs
    repository = AttendanceRepository(session)

    # In SQLite, without foreign key constraint enabled by default or with a mock error
    from unittest.mock import Mock, patch
    from sqlalchemy.exc import IntegrityError

    attendance = create_attendance()
    
    # Mocking IntegrityError without uq_attendance_employee_date
    with patch.object(session, "commit", side_effect=IntegrityError("FOREIGN KEY constraint failed", orig=None, params=None)):
        with pytest.raises(DatabaseError) as exc_info:
            repository.create(attendance)
        assert "integrity violation" in str(exc_info.value).lower()