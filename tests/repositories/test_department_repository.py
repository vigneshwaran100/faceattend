from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.department import Department
from app.repositories.department_repository import (
    DepartmentRepository,
)


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    return Session(engine)


def create_department() -> Department:
    now = datetime.now(timezone.utc)

    return Department(
        department_id="DEPT001",
        department_name="Engineering",
        created_at=now,
        updated_at=now,
    )


def test_create_department() -> None:
    session = create_test_session()

    repository = DepartmentRepository(session)

    result = repository.create(create_department())

    assert result.department_id == "DEPT001"
    assert result.department_name == "Engineering"


def test_get_by_id() -> None:
    session = create_test_session()

    repository = DepartmentRepository(session)

    repository.create(create_department())

    result = repository.get_by_id("DEPT001")

    assert result is not None
    assert result.department_id == "DEPT001"


def test_get_by_id_returns_none_for_missing_department() -> None:
    session = create_test_session()

    repository = DepartmentRepository(session)

    result = repository.get_by_id("UNKNOWN")

    assert result is None


def test_exists() -> None:
    session = create_test_session()

    repository = DepartmentRepository(session)

    repository.create(create_department())

    assert repository.exists("DEPT001") is True
    assert repository.exists("UNKNOWN") is False


def test_get_all() -> None:
    session = create_test_session()
    repository = DepartmentRepository(session)

    assert repository.get_all() == []

    repository.create(create_department())
    departments = repository.get_all()
    assert len(departments) == 1
    assert departments[0].department_id == "DEPT001"