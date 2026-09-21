from datetime import date, datetime, time, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_attendance_service,
    get_current_user,
    get_employee_repository,
)
from app.api.main import app
from app.models.attendance import Attendance
from app.models.attendance_summary import AttendanceSummary
from app.models.employee import Employee
from app.models.user import User


@pytest.fixture
def employee_repository() -> Mock:
    return Mock()


@pytest.fixture
def attendance_service() -> Mock:
    return Mock()


@pytest.fixture
def client(
    employee_repository: Mock,
    attendance_service: Mock,
) -> TestClient:
    now = datetime.now(timezone.utc)
    admin_user = User(
        id="ADMIN01",
        username="admin",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_current_user] = lambda: admin_user

    app.dependency_overrides[get_employee_repository] = (
        lambda: employee_repository
    )

    app.dependency_overrides[get_attendance_service] = (
        lambda: attendance_service
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def employee() -> Employee:
    return Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="vignesh@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="AI Engineer",
        status="active",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_get_attendance_history_returns_records(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    records = [
        Attendance(
            attendance_id="ATT001",
            employee_id="EMP001",
            attendance_date=date(2026, 8, 23),
            check_in=time(9, 0),
            check_out=time(18, 0),
            status="PRESENT",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]

    employee_repository.get_by_id.return_value = employee
    attendance_service.get_attendance_history_by_date_range.return_value = records

    response = client.get(
        "/employees/EMP001/attendance"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == "EMP001"
    assert len(data["attendance"]) == 1
    assert data["attendance"][0]["employee_id"] == "EMP001"
    assert data["attendance"][0]["attendance_date"] == "2026-08-23"

    employee_repository.get_by_id.assert_called_once_with(
        "EMP001"
    )

    attendance_service.get_attendance_history_by_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=None,
        end_date=None,
    )


def test_get_attendance_history_returns_empty_list(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee
    attendance_service.get_attendance_history_by_date_range.return_value = []

    response = client.get(
        "/employees/EMP001/attendance"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == "EMP001"
    assert data["attendance"] == []

    attendance_service.get_attendance_history_by_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=None,
        end_date=None,
    )


def test_get_attendance_history_returns_404_for_unknown_employee(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    employee_repository.get_by_id.return_value = None

    response = client.get(
        "/employees/INVALID001/attendance"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Employee not found: INVALID001"

    attendance_service.get_attendance_history_by_date_range.assert_not_called()


def test_get_attendance_history_with_date_range(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee
    attendance_service.get_attendance_history_by_date_range.return_value = []

    response = client.get(
        "/employees/EMP001/attendance",
        params={
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
        },
    )

    assert response.status_code == 200

    attendance_service.get_attendance_history_by_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )


def test_get_attendance_history_with_start_date(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee
    attendance_service.get_attendance_history_by_date_range.return_value = []

    response = client.get(
        "/employees/EMP001/attendance",
        params={"start_date": "2026-08-01"},
    )

    assert response.status_code == 200

    attendance_service.get_attendance_history_by_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=None,
    )


def test_get_attendance_history_with_end_date(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee
    attendance_service.get_attendance_history_by_date_range.return_value = []

    response = client.get(
        "/employees/EMP001/attendance",
        params={"end_date": "2026-08-31"},
    )

    assert response.status_code == 200

    attendance_service.get_attendance_history_by_date_range.assert_called_once_with(
        employee_id="EMP001",
        start_date=None,
        end_date=date(2026, 8, 31),
    )


def test_get_attendance_history_rejects_invalid_date(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    response = client.get(
        "/employees/EMP001/attendance",
        params={"start_date": "invalid-date"},
    )

    assert response.status_code == 422

    employee_repository.get_by_id.assert_not_called()
    attendance_service.get_attendance_history_by_date_range.assert_not_called()

def test_get_attendance_summary_returns_summary(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee

    attendance_service.get_attendance_summary.return_value = (
        AttendanceSummary(
            employee_id="EMP001",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 31),
            total_records=3,
            total_working_days=3,
            present_days=1,
            half_days=1,
            incomplete_days=0,
            absent_days=0,
            in_progress_days=1,
            total_working_hours=13.0,
            attendance_percentage=50.0,
        )
    )

    response = client.get(
        "/employees/EMP001/attendance/summary"
        "?start_date=2026-08-01"
        "&end_date=2026-08-31"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == "EMP001"
    assert data["start_date"] == "2026-08-01"
    assert data["end_date"] == "2026-08-31"
    assert data["total_records"] == 3
    assert data["total_working_days"] == 3
    assert data["present_days"] == 1
    assert data["half_days"] == 1
    assert data["incomplete_days"] == 0
    assert data["absent_days"] == 0
    assert data["in_progress_days"] == 1
    assert data["total_working_hours"] == 13.0
    assert data["attendance_percentage"] == 50.0

    employee_repository.get_by_id.assert_called_once_with("EMP001")

    attendance_service.get_attendance_summary.assert_called_once_with(
        employee_id="EMP001",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
    )   

def test_get_attendance_summary_returns_404_for_unknown_employee(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    employee_repository.get_by_id.return_value = None

    response = client.get(
        "/employees/INVALID001/attendance/summary"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Employee not found: INVALID001"

    attendance_service.get_attendance_summary.assert_not_called()

def test_get_attendance_summary_without_date_range(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    employee: Employee,
) -> None:
    employee_repository.get_by_id.return_value = employee

    attendance_service.get_attendance_summary.return_value = (
        AttendanceSummary(
            employee_id="EMP001",
            start_date=None,
            end_date=None,
            total_records=0,
            present_days=0,
            half_days=0,
            in_progress_days=0,
            total_working_hours=0.0,
        )
    )

    response = client.get(
        "/employees/EMP001/attendance/summary"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["employee_id"] == "EMP001"
    assert data["start_date"] is None
    assert data["end_date"] is None
    assert data["total_records"] == 0
    assert data["present_days"] == 0
    assert data["half_days"] == 0
    assert data["in_progress_days"] == 0
    assert data["total_working_hours"] == 0.0

    attendance_service.get_attendance_summary.assert_called_once_with(
        employee_id="EMP001",
        start_date=None,
        end_date=None,
    )


def test_get_attendance_summary_rejects_invalid_date_range(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    response = client.get(
        "/employees/EMP001/attendance/summary",
        params={
            "start_date": "2026-08-31",
            "end_date": "2026-08-01",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "start_date cannot be after end_date" in data["detail"]

    employee_repository.get_by_id.assert_not_called()
    attendance_service.get_attendance_summary.assert_not_called()