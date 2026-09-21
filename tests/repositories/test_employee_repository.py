from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models.department import DepartmentORM
from app.database.models.employee import EmployeeORM
from app.database.models.team import TeamORM
from app.models.employee import Employee
from app.repositories.employee_repository import EmployeeRepository


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    return Session(engine)


def create_employee() -> Employee:
    now = datetime.now(timezone.utc)

    return Employee(
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


def seed_dependencies(session: Session) -> None:
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


def test_create_employee() -> None:
    session = create_test_session()
    seed_dependencies(session)

    repository = EmployeeRepository(session)

    employee = create_employee()

    result = repository.create(employee)

    assert result.employee_id == "EMP001"
    assert result.name == "Vigneshwaran"


def test_get_by_id() -> None:
    session = create_test_session()
    seed_dependencies(session)

    repository = EmployeeRepository(session)

    employee = create_employee()

    repository.create(employee)

    result = repository.get_by_id("EMP001")

    assert result is not None
    assert result.employee_id == "EMP001"


def test_get_by_id_returns_none_for_missing_employee() -> None:
    session = create_test_session()

    repository = EmployeeRepository(session)

    result = repository.get_by_id("UNKNOWN")

    assert result is None


def test_get_by_email() -> None:
    session = create_test_session()
    seed_dependencies(session)

    repository = EmployeeRepository(session)

    repository.create(create_employee())

    result = repository.get_by_email(
        "vigneshwaran@example.com"
    )

    assert result is not None
    assert result.employee_id == "EMP001"


def test_exists() -> None:
    session = create_test_session()
    seed_dependencies(session)

    repository = EmployeeRepository(session)

    repository.create(create_employee())

    assert repository.exists("EMP001") is True
    assert repository.exists("UNKNOWN") is False


def test_update_employee() -> None:
    session = create_test_session()
    seed_dependencies(session)

    repository = EmployeeRepository(session)

    employee = create_employee()

    repository.create(employee)

    updated = Employee(
        employee_id="EMP001",
        name="Vigneshwaran Updated",
        email="updated@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Senior Engineer",
        status="active",
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )

    result = repository.update(updated)

    assert result.name == "Vigneshwaran Updated"
    assert result.email == "updated@example.com"
    assert result.designation == "Senior Engineer"