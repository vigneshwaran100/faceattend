from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.repositories.user_repository import UserRepository


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_and_get_user_by_id_and_username() -> None:
    session = create_test_session()
    repo = UserRepository(session)

    now = datetime.now(timezone.utc)
    user = User(
        id="USR001",
        username="admin",
        password_hash="hashed_pw_123",
        role="admin",
        status="active",
        created_at=now,
        updated_at=now,
    )

    created = repo.create(user)
    assert created.id == "USR001"
    assert created.username == "admin"
    assert created.role == "admin"
    assert created.status == "active"

    # By ID
    by_id = repo.get_by_id("USR001")
    assert by_id is not None
    assert by_id.username == "admin"

    # By username (case insensitive)
    by_username = repo.get_by_username("ADMIN")
    assert by_username is not None
    assert by_username.id == "USR001"

    # Exists check
    assert repo.exists_by_username("admin") is True
    assert repo.exists_by_username("nonexistent") is False


def test_get_nonexistent_user_returns_none() -> None:
    session = create_test_session()
    repo = UserRepository(session)

    assert repo.get_by_id("NONEXISTENT") is None
    assert repo.get_by_username("nonexistent") is None


def test_duplicate_username_raises_database_error() -> None:
    session = create_test_session()
    repo = UserRepository(session)

    now = datetime.now(timezone.utc)
    user1 = User(
        id="USR001",
        username="admin",
        password_hash="hashed_pw_1",
        role="admin",
        status="active",
        created_at=now,
        updated_at=now,
    )
    repo.create(user1)

    user2 = User(
        id="USR002",
        username="admin",
        password_hash="hashed_pw_2",
        role="security",
        status="active",
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(DatabaseError):
        repo.create(user2)
