import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.user import UserORM
from app.infrastructure.database_error import DatabaseError
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, user: User) -> User:
        try:
            record = UserORM(
                id=user.id,
                username=user.username,
                password_hash=user.password_hash,
                role=user.role,
                status=user.status,
                created_at=user.created_at or datetime.now(),
                updated_at=user.updated_at or datetime.now(),
            )

            self._session.add(record)
            self._session.commit()
            self._session.refresh(record)

            return self._to_domain(record)

        except SQLAlchemyError as error:
            self._session.rollback()
            logger.error(
                "Database error creating user | username=%s | error=%s",
                user.username,
                error,
            )
            raise DatabaseError("Failed to create user") from error

    def get_by_id(self, user_id: str) -> User | None:
        try:
            statement = select(UserORM).where(UserORM.id == user_id)
            record = self._session.scalar(statement)
            if record is None:
                return None
            return self._to_domain(record)

        except SQLAlchemyError as error:
            logger.error(
                "Database error fetching user by id | user_id=%s | error=%s",
                user_id,
                error,
            )
            raise DatabaseError("Failed to fetch user by id") from error

    def get_by_username(self, username: str) -> User | None:
        try:
            statement = select(UserORM).where(
                UserORM.username == username.strip().lower()
            )
            record = self._session.scalar(statement)
            if record is None:
                return None
            return self._to_domain(record)

        except SQLAlchemyError as error:
            logger.error(
                "Database error fetching user by username | username=%s | error=%s",
                username,
                error,
            )
            raise DatabaseError("Failed to fetch user by username") from error

    def exists_by_username(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    @staticmethod
    def _to_domain(record: UserORM) -> User:
        return User(
            id=record.id,
            username=record.username,
            password_hash=record.password_hash,
            role=record.role,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
