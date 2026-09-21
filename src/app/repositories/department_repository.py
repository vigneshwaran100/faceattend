from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.department import DepartmentORM
from app.models.department import Department


class DepartmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, department: Department) -> Department:
        entity = DepartmentORM(
            department_id=department.department_id,
            department_name=department.department_name,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )

        self._session.add(entity)
        self._session.flush()

        return self._to_domain(entity)

    def get_by_id(
        self,
        department_id: str,
    ) -> Department | None:
        statement = select(DepartmentORM).where(
            DepartmentORM.department_id == department_id
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    def exists(self, department_id: str) -> bool:
        statement = select(
            DepartmentORM.department_id
        ).where(
            DepartmentORM.department_id == department_id
        )

        return self._session.scalar(statement) is not None

    def get_all(self) -> list[Department]:
        statement = select(DepartmentORM).order_by(
            DepartmentORM.department_id
        )

        entities = self._session.scalars(statement).all()

        return [self._to_domain(entity) for entity in entities]

    def get_by_name(
        self,
        department_name: str,
    ) -> Department | None:
        statement = select(DepartmentORM).where(
            DepartmentORM.department_name == department_name
        )

        entity = self._session.scalar(statement)

        if entity is None:
            return None

        return self._to_domain(entity)

    @staticmethod
    def _to_domain(
        entity: DepartmentORM,
    ) -> Department:
        return Department(
            department_id=entity.department_id,
            department_name=entity.department_name,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )