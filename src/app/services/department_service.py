import logging
from datetime import datetime, timezone

from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository

logger = logging.getLogger(__name__)


class DepartmentService:
    def __init__(self, repository: DepartmentRepository) -> None:
        self._repository = repository

    def create_department(
        self,
        *,
        department_id: str,
        department_name: str,
    ) -> Department:
        department_id = department_id.strip()
        department_name = department_name.strip()

        if not department_id:
            raise ValueError("Department ID cannot be empty")

        if not department_name:
            raise ValueError("Department name cannot be empty")

        if self._repository.exists(department_id):
            raise ValueError(
                f"Department already exists: {department_id}"
            )

        if self._repository.get_by_name(department_name):
            raise ValueError(
                f"Department name already exists: {department_name}"
            )

        now = datetime.now(timezone.utc)

        department = Department(
            department_id=department_id,
            department_name=department_name,
            created_at=now,
            updated_at=now,
        )

        created = self._repository.create(department)

        logger.info(
            "Department created successfully | department_id=%s | name=%s",
            created.department_id,
            created.department_name,
        )

        return created

    def get_department(
        self,
        department_id: str,
    ) -> Department | None:
        department_id = department_id.strip()
        if not department_id:
            raise ValueError("Department ID cannot be empty")

        return self._repository.get_by_id(department_id)

    def list_departments(self) -> list[Department]:
        return self._repository.get_all()

