from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_department_service,
    get_employee_repository,
    get_team_service,
)
from app.api.main import app
from app.infrastructure.database_error import DatabaseError
from app.models.department import Department
from app.models.employee import Employee
from app.models.team import Team
from app.models.user import User


@pytest.fixture
def mock_employee_repository() -> Mock:
    return Mock()


@pytest.fixture
def mock_department_service() -> Mock:
    return Mock()


@pytest.fixture
def mock_team_service() -> Mock:
    return Mock()


@pytest.fixture
def authenticated_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id="USER001",
        username="john_doe",
        password_hash="hash",
        role="security",
        status="active",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client(
    mock_employee_repository: Mock,
    mock_department_service: Mock,
    mock_team_service: Mock,
    authenticated_user: User,
) -> TestClient:
    app.dependency_overrides[get_current_user] = lambda: authenticated_user
    app.dependency_overrides[get_employee_repository] = lambda: mock_employee_repository
    app.dependency_overrides[get_department_service] = lambda: mock_department_service
    app.dependency_overrides[get_team_service] = lambda: mock_team_service

    yield TestClient(app)
    app.dependency_overrides.clear()



# ==========================================
# GET /employees Tests
# ==========================================


def test_get_employees_success(
    client: TestClient,
    mock_employee_repository: Mock,
) -> None:
    now = datetime.now(timezone.utc)
    mock_employee_repository.get_all_active.return_value = [
        Employee(
            employee_id="EMP001",
            name="Alice Smith",
            email="alice@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation="Software Engineer",
            status="active",
            created_at=now,
            updated_at=now,
        ),
        Employee(
            employee_id="EMP002",
            name="Bob Jones",
            email="bob@example.com",
            team_id="TEAM002",
            department_id="DEPT001",
            designation="Product Manager",
            status="active",
            created_at=now,
            updated_at=now,
        ),
    ]

    response = client.get("/employees")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["employee_id"] == "EMP001"
    assert data[0]["name"] == "Alice Smith"
    assert data[0]["email"] == "alice@example.com"
    assert data[0]["status"] == "active"
    assert data[1]["employee_id"] == "EMP002"
    assert data[1]["name"] == "Bob Jones"


def test_get_employees_empty(
    client: TestClient,
    mock_employee_repository: Mock,
) -> None:
    mock_employee_repository.get_all_active.return_value = []

    response = client.get("/employees")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_employees_database_error(
    client: TestClient,
    mock_employee_repository: Mock,
) -> None:
    mock_employee_repository.get_all_active.side_effect = DatabaseError("Database failure")

    response = client.get("/employees")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# ==========================================
# GET /departments Tests
# ==========================================


def test_get_departments_success(
    client: TestClient,
    mock_department_service: Mock,
) -> None:
    now = datetime.now(timezone.utc)
    mock_department_service.list_departments.return_value = [
        Department(
            department_id="DEPT001",
            department_name="Engineering",
            created_at=now,
            updated_at=now,
        ),
        Department(
            department_id="DEPT002",
            department_name="Human Resources",
            created_at=now,
            updated_at=now,
        ),
    ]

    response = client.get("/departments")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["department_id"] == "DEPT001"
    assert data[0]["department_name"] == "Engineering"
    assert data[1]["department_id"] == "DEPT002"
    assert data[1]["department_name"] == "Human Resources"


def test_get_departments_empty(
    client: TestClient,
    mock_department_service: Mock,
) -> None:
    mock_department_service.list_departments.return_value = []

    response = client.get("/departments")

    assert response.status_code == 200
    assert response.json() == []


def test_get_departments_database_error(
    client: TestClient,
    mock_department_service: Mock,
) -> None:
    mock_department_service.list_departments.side_effect = DatabaseError("DB down")

    response = client.get("/departments")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# ==========================================
# GET /teams Tests
# ==========================================


def test_get_teams_success(
    client: TestClient,
    mock_team_service: Mock,
) -> None:
    now = datetime.now(timezone.utc)
    mock_team_service.list_teams.return_value = [
        Team(
            team_id="TEAM001",
            team_name="Core Backend",
            created_at=now,
            updated_at=now,
        ),
        Team(
            team_id="TEAM002",
            team_name="Computer Vision",
            created_at=now,
            updated_at=now,
        ),
    ]

    response = client.get("/teams")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["team_id"] == "TEAM001"
    assert data[0]["team_name"] == "Core Backend"
    assert data[1]["team_id"] == "TEAM002"
    assert data[1]["team_name"] == "Computer Vision"


def test_get_teams_empty(
    client: TestClient,
    mock_team_service: Mock,
) -> None:
    mock_team_service.list_teams.return_value = []

    response = client.get("/teams")

    assert response.status_code == 200
    assert response.json() == []


def test_get_teams_database_error(
    client: TestClient,
    mock_team_service: Mock,
) -> None:
    mock_team_service.list_teams.side_effect = DatabaseError("DB down")

    response = client.get("/teams")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"
