from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service
from app.api.main import app
from app.infrastructure.database_error import DatabaseError
from app.models.user import User


@pytest.fixture
def auth_service() -> Mock:
    return Mock()


@pytest.fixture
def client(auth_service: Mock) -> TestClient:
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_login_successful(
    client: TestClient,
    auth_service: Mock,
) -> None:
    user = User(
        id="USR001",
        username="admin",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )
    auth_service.authenticate.return_value = user
    auth_service.create_access_token.return_value = "mocked.jwt.token"

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "CorrectPassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "mocked.jwt.token"
    assert data["token_type"] == "bearer"

    auth_service.authenticate.assert_called_once_with(
        username="admin",
        password="CorrectPassword123",
    )
    auth_service.create_access_token.assert_called_once_with(user)


def test_login_invalid_credentials_returns_401(
    client: TestClient,
    auth_service: Mock,
) -> None:
    auth_service.authenticate.side_effect = ValueError(
        "Invalid username or password"
    )

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "WrongPassword"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "invalid username or password" in data["detail"].lower()


def test_login_inactive_user_returns_401(
    client: TestClient,
    auth_service: Mock,
) -> None:
    auth_service.authenticate.side_effect = ValueError(
        "User account is inactive"
    )

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Password123"},
    )

    assert response.status_code == 401
    data = response.json()
    assert "inactive" in data["detail"].lower()


def test_login_database_error_returns_500(
    client: TestClient,
    auth_service: Mock,
) -> None:
    auth_service.authenticate.side_effect = DatabaseError("Database unavailable")

    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "Password123"},
    )

    assert response.status_code == 500
    data = response.json()
    assert "database error" in data["detail"].lower()
