import logging
from datetime import datetime, timezone

from app.models.employee import Employee
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.team_repository import TeamRepository

logger = logging.getLogger(__name__)


class EmployeeRegistrationService:
    def __init__(
        self,
        employee_repository: EmployeeRepository,
        team_repository: TeamRepository,
        department_repository: DepartmentRepository,
    ) -> None:
        self._employee_repository = employee_repository
        self._team_repository = team_repository
        self._department_repository = department_repository

    def register(
        self,
        *,
        employee_id: str,
        name: str,
        email: str,
        team_id: str,
        department_id: str | None,
        designation: str | None,
    ) -> Employee:

        employee_id = employee_id.strip()
        name = name.strip()
        email = email.strip().lower()
        team_id = team_id.strip()

        if not employee_id:
            raise ValueError("Employee ID cannot be empty")

        if not name:
            raise ValueError("Employee name cannot be empty")

        if not email:
            raise ValueError("Employee email cannot be empty")

        if not team_id:
            raise ValueError("Team ID cannot be empty")

        if self._employee_repository.exists(employee_id):
            raise ValueError(
                f"Employee already exists: {employee_id}"
            )

        if self._employee_repository.get_by_email(email):
            raise ValueError(
                f"Employee email already exists: {email}"
            )

        if not self._team_repository.exists(team_id):
            raise ValueError(
                f"Team does not exist: {team_id}"
            )

        if (
            department_id is not None
            and not self._department_repository.exists(
                department_id
            )
        ):
            raise ValueError(
                f"Department does not exist: {department_id}"
            )

        now = datetime.now(timezone.utc)

        employee = Employee(
            employee_id=employee_id,
            name=name,
            email=email,
            team_id=team_id,
            department_id=department_id,
            designation=designation,
            status="active",
            created_at=now,
            updated_at=now,
        )

        created = self._employee_repository.create(employee)

        logger.info(
            "Employee registered successfully | employee_id=%s | name=%s | team_id=%s",
            employee.employee_id,
            employee.name,
            employee.team_id,
        )

        return created

    def update(
        self,
        *,
        employee_id: str,
        name: str,
        email: str,
        team_id: str,
        department_id: str | None,
        designation: str | None,
        status: str = "active",
    ) -> Employee:
        employee_id = employee_id.strip()
        name = name.strip()
        email = email.strip().lower()
        team_id = team_id.strip()
        status = status.strip().lower()

        if not employee_id:
            raise ValueError("Employee ID cannot be empty")

        if not name:
            raise ValueError("Employee name cannot be empty")

        if not email:
            raise ValueError("Employee email cannot be empty")

        if not team_id:
            raise ValueError("Team ID cannot be empty")

        if not status:
            raise ValueError("Status cannot be empty")

        existing = self._employee_repository.get_by_id(employee_id)
        if existing is None:
            raise ValueError(f"Employee not found: {employee_id}")

        email_owner = self._employee_repository.get_by_email(email)
        if email_owner is not None and email_owner.employee_id != employee_id:
            raise ValueError(f"Employee email already exists: {email}")

        if not self._team_repository.exists(team_id):
            raise ValueError(f"Team does not exist: {team_id}")

        if (
            department_id is not None
            and not self._department_repository.exists(department_id)
        ):
            raise ValueError(f"Department does not exist: {department_id}")

        now = datetime.now(timezone.utc)

        employee = Employee(
            employee_id=employee_id,
            name=name,
            email=email,
            team_id=team_id,
            department_id=department_id,
            designation=designation,
            status=status,
            created_at=existing.created_at,
            updated_at=now,
        )

        updated = self._employee_repository.update(employee)

        logger.info(
            "Employee updated successfully | employee_id=%s | name=%s | team_id=%s | status=%s",
            updated.employee_id,
            updated.name,
            updated.team_id,
            updated.status,
        )

        return updated

    def set_status(
        self,
        *,
        employee_id: str,
        status: str,
    ) -> Employee:
        employee_id = employee_id.strip()
        status = status.strip().lower()

        if not employee_id:
            raise ValueError("Employee ID cannot be empty")

        if status not in {"active", "inactive"}:
            raise ValueError(
                f"Invalid status: '{status}'. Status must be 'active' or 'inactive'"
            )

        existing = self._employee_repository.get_by_id(employee_id)
        if existing is None:
            raise ValueError(f"Employee not found: {employee_id}")

        now = datetime.now(timezone.utc)

        employee = Employee(
            employee_id=existing.employee_id,
            name=existing.name,
            email=existing.email,
            team_id=existing.team_id,
            department_id=existing.department_id,
            designation=existing.designation,
            status=status,
            created_at=existing.created_at,
            updated_at=now,
        )

        updated = self._employee_repository.update(employee)

        logger.info(
            "Employee status updated | employee_id=%s | status=%s",
            updated.employee_id,
            updated.status,
        )

        return updated