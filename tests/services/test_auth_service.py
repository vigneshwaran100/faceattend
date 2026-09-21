from datetime import timedelta
from unittest.mock import Mock

import pytest

from app.models.user import User
from app.services.auth_service import AuthService


def test_password_hashing_and_verification() -> None:
    repo = Mock()
    service = AuthService(repo)

    password = "SuperSecretPassword123"
    hashed = service.hash_password(password)

    assert hashed != password
    assert service.verify_password(password, hashed) is True
    assert service.verify_password("WrongPassword", hashed) is False
    assert service.verify_password("", hashed) is False
    assert service.verify_password(password, "") is False


def test_create_user_success() -> None:
    repo = Mock()
    repo.exists_by_username.return_value = False
    repo.create.side_effect = lambda user: user

    service = AuthService(repo)
    user = service.create_user(
        username="SecurityOfficer1",
        password="MySecretPassword123",
        role="security",
    )

    assert user.username == "securityofficer1"
    assert user.role == "security"
    assert user.status == "active"
    assert service.verify_password("MySecretPassword123", user.password_hash) is True
    repo.create.assert_called_once()


def test_create_user_duplicate_username_raises() -> None:
    repo = Mock()
    repo.exists_by_username.return_value = True

    service = AuthService(repo)
    with pytest.raises(ValueError, match="already exists"):
        service.create_user(
            username="admin",
            password="Password123",
        )


def test_create_user_short_password_raises() -> None:
    repo = Mock()
    repo.exists_by_username.return_value = False

    service = AuthService(repo)
    with pytest.raises(ValueError, match="at least 6 characters"):
        service.create_user(
            username="admin",
            password="123",
        )


def test_authenticate_success() -> None:
    repo = Mock()
    service = AuthService(repo)

    hashed = service.hash_password("ValidPassword123")
    user = User(
        id="USR001",
        username="admin",
        password_hash=hashed,
        role="admin",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )
    repo.get_by_username.return_value = user

    authenticated = service.authenticate("ADMIN", "ValidPassword123")
    assert authenticated.id == "USR001"
    assert authenticated.username == "admin"


def test_authenticate_unknown_user_raises() -> None:
    repo = Mock()
    repo.get_by_username.return_value = None

    service = AuthService(repo)
    with pytest.raises(ValueError, match="Invalid username or password"):
        service.authenticate("nonexistent", "Password123")


def test_authenticate_wrong_password_raises() -> None:
    repo = Mock()
    service = AuthService(repo)

    hashed = service.hash_password("CorrectPassword")
    user = User(
        id="USR001",
        username="admin",
        password_hash=hashed,
        role="admin",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )
    repo.get_by_username.return_value = user

    with pytest.raises(ValueError, match="Invalid username or password"):
        service.authenticate("admin", "WrongPassword")


def test_authenticate_inactive_user_raises() -> None:
    repo = Mock()
    service = AuthService(repo)

    hashed = service.hash_password("CorrectPassword")
    user = User(
        id="USR001",
        username="admin",
        password_hash=hashed,
        role="admin",
        status="inactive",
        created_at=Mock(),
        updated_at=Mock(),
    )
    repo.get_by_username.return_value = user

    with pytest.raises(ValueError, match="inactive"):
        service.authenticate("admin", "CorrectPassword")


def test_jwt_token_generation_and_decoding() -> None:
    repo = Mock()
    service = AuthService(repo)

    user = User(
        id="USR001",
        username="admin",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )

    token = service.create_access_token(user, expires_delta=timedelta(minutes=30))
    assert isinstance(token, str)

    payload = service.decode_token(token)
    assert payload["sub"] == "USR001"
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_token_expired_raises() -> None:
    repo = Mock()
    service = AuthService(repo)

    user = User(
        id="USR001",
        username="admin",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=Mock(),
        updated_at=Mock(),
    )

    token = service.create_access_token(user, expires_delta=timedelta(seconds=-10))

    with pytest.raises(ValueError, match="Invalid or expired token"):
        service.decode_token(token)


def test_decode_token_tampered_raises() -> None:
    repo = Mock()
    service = AuthService(repo)

    with pytest.raises(ValueError, match="Invalid or expired token"):
        service.decode_token("invalid.jwt.token")
