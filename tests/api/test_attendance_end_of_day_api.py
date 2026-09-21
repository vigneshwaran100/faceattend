from datetime import date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_attendance_service,
    get_current_user,
    get_employee_repository,
    get_scanner_audit_service,
)
from app.api.main import app
from app.infrastructure.database_error import DatabaseError
from app.models.employee import Employee
from app.models.end_of_day_summary import EndOfDaySummary
from app.models.user import User


@pytest.fixture
def employee_repository() -> Mock:
    return Mock()


@pytest.fixture
def attendance_service() -> Mock:
    return Mock()


@pytest.fixture
def scanner_audit_service() -> Mock:
    return Mock()


@pytest.fixture
def client(
    employee_repository: Mock,
    attendance_service: Mock,
    scanner_audit_service: Mock,
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
    app.dependency_overrides[get_scanner_audit_service] = (
        lambda: scanner_audit_service
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_post_end_of_day_default_today(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    scanner_audit_service: Mock,
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

    attendance_service.process_end_of_day.return_value = EndOfDaySummary(
        attendance_date=now.date(),
        present=1,
        half_day=0,
        incomplete=0,
        absent=0,
        total_processed=1,
    )

    response = client.post("/attendance/end-of-day")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == str(now.date())
    assert data["present"] == 1
    assert data["half_day"] == 0
    assert data["incomplete"] == 0
    assert data["absent"] == 0
    assert data["total_processed"] == 1
    assert data["message"] == "End-of-day attendance finalization completed successfully"

    scanner_audit_service.log_event.assert_called_once()
    call_kwargs = scanner_audit_service.log_event.call_args[1]
    assert call_kwargs["status"] == "SUCCESS"
    assert call_kwargs["event_type"] == "end_of_day_finalization"


def test_post_end_of_day_with_custom_date(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    scanner_audit_service: Mock,
) -> None:
    target_date = date(2026, 8, 28)
    employee_repository.get_all_active.return_value = []

    attendance_service.process_end_of_day.return_value = EndOfDaySummary(
        attendance_date=target_date,
        present=2,
        half_day=1,
        incomplete=1,
        absent=3,
        total_processed=7,
    )

    response = client.post(f"/attendance/end-of-day?attendance_date={target_date}")

    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-08-28"
    assert data["present"] == 2
    assert data["half_day"] == 1
    assert data["incomplete"] == 1
    assert data["absent"] == 3
    assert data["total_processed"] == 7


def test_post_end_of_day_database_error_returns_500(
    client: TestClient,
    employee_repository: Mock,
    attendance_service: Mock,
    scanner_audit_service: Mock,
) -> None:
    employee_repository.get_all_active.side_effect = DatabaseError("Database unavailable")

    response = client.post("/attendance/end-of-day")

    assert response.status_code == 500
    data = response.json()
    assert "database error" in data["detail"].lower()

    scanner_audit_service.log_event.assert_called_once()
    call_kwargs = scanner_audit_service.log_event.call_args[1]
    assert call_kwargs["status"] == "FAILURE"
