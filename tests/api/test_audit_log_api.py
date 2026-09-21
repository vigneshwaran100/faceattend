from datetime import date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_scanner_audit_service,
)
from app.api.main import app
from app.infrastructure.database_error import DatabaseError
from app.models.paginated_audit_logs import PaginatedAuditLogs
from app.models.scanner_audit_log import ScannerAuditLog
from app.models.user import User


@pytest.fixture
def audit_service() -> Mock:
    return Mock()


@pytest.fixture
def client(audit_service: Mock) -> TestClient:
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
    app.dependency_overrides[get_scanner_audit_service] = (
        lambda: audit_service
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_audit_logs_returns_paginated_list(
    client: TestClient,
    audit_service: Mock,
) -> None:
    now = datetime(2026, 8, 29, 10, 0, 0)
    log_item = ScannerAuditLog(
        log_id="LOG001",
        scanner_type="check_in",
        event_type="attendance_success",
        status="SUCCESS",
        employee_id="EMP001",
        similarity=0.85,
        message="Check-in recorded",
        created_at=now,
    )

    audit_service.get_logs.return_value = PaginatedAuditLogs(
        items=[log_item],
        total=1,
        page=1,
        page_size=20,
        total_pages=1,
    )

    response = client.get("/audit-logs")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["log_id"] == "LOG001"
    assert item["scanner_type"] == "check_in"
    assert item["event_type"] == "attendance_success"
    assert item["status"] == "SUCCESS"
    assert item["employee_id"] == "EMP001"
    assert item["similarity"] == 0.85
    assert item["message"] == "Check-in recorded"

    audit_service.get_logs.assert_called_once_with(
        employee_id=None,
        event_type=None,
        scanner_type=None,
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
    )


def test_get_audit_logs_with_filters(
    client: TestClient,
    audit_service: Mock,
) -> None:
    audit_service.get_logs.return_value = PaginatedAuditLogs(
        items=[],
        total=0,
        page=2,
        page_size=10,
        total_pages=0,
    )

    response = client.get(
        "/audit-logs"
        "?employee_id=EMP001"
        "&event_type=unknown_face"
        "&scanner_type=check_in"
        "&start_date=2026-08-01"
        "&end_date=2026-08-31"
        "&page=2"
        "&page_size=10"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["page_size"] == 10
    assert data["items"] == []

    audit_service.get_logs.assert_called_once_with(
        employee_id="EMP001",
        event_type="unknown_face",
        scanner_type="check_in",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        page=2,
        page_size=10,
    )


def test_get_audit_logs_rejects_invalid_date_range(
    client: TestClient,
    audit_service: Mock,
) -> None:
    response = client.get(
        "/audit-logs?start_date=2026-08-31&end_date=2026-08-01"
    )

    assert response.status_code == 400
    data = response.json()
    assert "start_date cannot be after end_date" in data["detail"]
    audit_service.get_logs.assert_not_called()


def test_get_audit_logs_rejects_invalid_page(
    client: TestClient,
    audit_service: Mock,
) -> None:
    response = client.get("/audit-logs?page=0")
    assert response.status_code == 422
    audit_service.get_logs.assert_not_called()


def test_get_audit_logs_database_error_returns_500(
    client: TestClient,
    audit_service: Mock,
) -> None:
    audit_service.get_logs.side_effect = DatabaseError("Database failure")

    response = client.get("/audit-logs")
    assert response.status_code == 500
    data = response.json()
    assert "database error" in data["detail"].lower()
