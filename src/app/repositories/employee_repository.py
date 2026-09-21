from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.employee import EmployeeORM
from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, employee: Employee) -> Employee:
        entity = EmployeeORM(
            employee_id=employee.employee_id,
            name=employee.name,
            email=employee.email,
            team_id=employee.team_id,
            department_id=employee.department_id,
            designation=employee.designation,
            status=employee.status,
            created_at=employee.created_at,
            updated_at=employee.updated_at,
        )

        self._session.add(entity)
        self._session.flush()

        return self._to_domain(entity)

    def get_by_id(self, employee_id: str) -> Employee | None:
        statement = select(EmployeeORM).where(
            EmployeeORM.employee_id == employee_id
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    def get_by_email(self, email: str) -> Employee | None:
        statement = select(EmployeeORM).where(
            EmployeeORM.email == email
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    def exists(self, employee_id: str) -> bool:
        statement = select(EmployeeORM.employee_id).where(
            EmployeeORM.employee_id == employee_id
        )

        return self._session.scalar(statement) is not None

    def get_all_active(self) -> list[Employee]:
        statement = (
            select(EmployeeORM)
            .where(EmployeeORM.status == "active")
            .order_by(EmployeeORM.employee_id)
        )

        entities = self._session.scalars(statement).all()

        return [self._to_domain(entity) for entity in entities]

    def update(self, employee: Employee) -> Employee:
        entity = self._session.get(
            EmployeeORM,
            employee.employee_id,
        )

        if entity is None:
            raise ValueError(
                f"Employee not found: {employee.employee_id}"
            )

        entity.name = employee.name
        entity.email = employee.email
        entity.team_id = employee.team_id
        entity.department_id = employee.department_id
        entity.designation = employee.designation
        entity.status = employee.status
        entity.updated_at = datetime.now(timezone.utc)

        self._session.flush()

        return self._to_domain(entity)

    @staticmethod
    def _to_domain(entity: EmployeeORM) -> Employee:
        return Employee(
            employee_id=entity.employee_id,
            name=entity.name,
            email=entity.email,
            team_id=entity.team_id,
            department_id=entity.department_id,
            designation=entity.designation,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )