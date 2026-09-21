from datetime import date, datetime, time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_attendance_service,
    get_current_user,
    get_employee_repository,
)
from app.api.main import app
from app.infrastructure.database_error import DatabaseError
from app.models.daily_attendance_report import (
    DailyAttendanceItem,
    DailyAttendanceReport,
)
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
    now = datetime.now()
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


def test_get_daily_report_default_today(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    now = datetime.now()
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
        )
    ]
    employee_repository.get_all_active.return_value = active_employees

    attendance_service.get_daily_attendance_report.return_value = (
        DailyAttendanceReport(
            attendance_date=now.date(),
            total_employees=1,
            records=[
                DailyAttendanceItem(
                    employee_id="EMP001",
                    name="Vigneshwaran",
                    check_in=time(9, 0),
                    check_out=time(18, 0),
                    working_hours=9.0,
                    status="present",
                )
            ],
        )
    )

    response = client.get("/attendance")

    assert response.status_code == 200
    data = response.json()
    assert data["attendance_date"] == str(now.date())
    assert data["total_employees"] == 1
    assert len(data["records"]) == 1
    record = data["records"][0]
    assert record["employee_id"] == "EMP001"
    assert record["name"] == "Vigneshwaran"
    assert record["check_in"] == "09:00:00"
    assert record["check_out"] == "18:00:00"
    assert record["working_hours"] == 9.0
    assert record["status"] == "present"


def test_get_daily_report_with_custom_date(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    target_date = date(2026, 8, 28)
    employee_repository.get_all_active.return_value = []

    attendance_service.get_daily_attendance_report.return_value = (
        DailyAttendanceReport(
            attendance_date=target_date,
            total_employees=0,
            records=[],
        )
    )

    response = client.get(f"/attendance?attendance_date={target_date}")

    assert response.status_code == 200
    data = response.json()
    assert data["attendance_date"] == "2026-08-28"
    assert data["total_employees"] == 0
    assert data["records"] == []


def test_get_daily_report_database_error_returns_500(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
) -> None:
    employee_repository.get_all_active.side_effect = DatabaseError("DB down")

    response = client.get("/attendance")

    assert response.status_code == 500
    data = response.json()
    assert "database error" in data["detail"].lower()
