from datetime import datetime, timezone

import pytest

from app.models.department import Department
from app.models.employee import Employee
from app.models.team import Team
from app.services.employee_registration_service import (
    EmployeeRegistrationService,
)


class FakeEmployeeRepository:
    def __init__(self) -> None:
        self.employees: dict[str, Employee] = {}

    def create(self, employee: Employee) -> Employee:
        self.employees[employee.employee_id] = employee
        return employee

    def get_by_email(self, email: str) -> Employee | None:
        return next(
            (
                employee
                for employee in self.employees.values()
                if employee.email == email
            ),
            None,
        )

    def exists(self, employee_id: str) -> bool:
        return employee_id in self.employees


class FakeTeamRepository:
    def __init__(self, team_ids: set[str]) -> None:
        self.team_ids = team_ids

    def exists(self, team_id: str) -> bool:
        return team_id in self.team_ids


class FakeDepartmentRepository:
    def __init__(self, department_ids: set[str]) -> None:
        self.department_ids = department_ids

    def exists(self, department_id: str) -> bool:
        return department_id in self.department_ids


def create_service() -> tuple[
    EmployeeRegistrationService,
    FakeEmployeeRepository,
]:
    employee_repository = FakeEmployeeRepository()

    team_repository = FakeTeamRepository(
        {"TEAM001"}
    )

    department_repository = FakeDepartmentRepository(
        {"DEPT001"}
    )

    service = EmployeeRegistrationService(
        employee_repository=employee_repository,
        team_repository=team_repository,
        department_repository=department_repository,
    )

    return service, employee_repository


def test_register_employee() -> None:
    service, repository = create_service()

    employee = service.register(
        employee_id="EMP001",
        name=" Vigneshwaran ",
        email="VIGNESHWARAN@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Software Engineer",
    )

    assert employee.employee_id == "EMP001"
    assert employee.name == "Vigneshwaran"
    assert employee.email == "vigneshwaran@example.com"
    assert employee.status == "active"

    assert repository.exists("EMP001") is True


def test_rejects_duplicate_employee_id() -> None:
    service, _ = create_service()

    service.register(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="v@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation=None,
    )

    with pytest.raises(
        ValueError,
        match="Employee already exists",
    ):
        service.register(
            employee_id="EMP001",
            name="Another Person",
            email="another@example.com",
            team_id="TEAM001",
            department_id="DEPT001",
            designation=None,
        )


def test_rejects_duplicate_email() -> None:
    service, _ = create_service()

    service.register(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="v@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation=None,
    )

    with pytest.raises(
        ValueError,
        match="Employee email already exists",
    ):
        service.register(
            employee_id="EMP002",
            name="Another Person",
            email="V@EXAMPLE.COM",
            team_id="TEAM001",
            department_id="DEPT001",
            designation=None,
        )


def test_rejects_unknown_team() -> None:
    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Team does not exist",
    ):
        service.register(
            employee_id="EMP001",
            name="Vigneshwaran",
            email="v@example.com",
            team_id="UNKNOWN",
            department_id="DEPT001",
            designation=None,
        )


def test_rejects_unknown_department() -> None:
    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Department does not exist",
    ):
        service.register(
            employee_id="EMP001",
            name="Vigneshwaran",
            email="v@example.com",
            team_id="TEAM001",
            department_id="UNKNOWN",
            designation=None,
        )


def test_rejects_empty_employee_id() -> None:
    service, _ = create_service()

    with pytest.raises(
        ValueError,
        match="Employee ID cannot be empty",
    ):
        service.register(
            employee_id=" ",
            name="Vigneshwaran",
            email="v@example.com",
            team_id="TEAM001",
            department_id=None,
            designation=None,
        )