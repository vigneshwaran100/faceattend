from datetime import datetime, timedelta, timezone
import logging
from typing import Any
from uuid import uuid4

import bcrypt
import jwt

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        if not password or not password_hash:
            return False
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception:
            return False

    def create_user(
        self,
        *,
        username: str,
        password: str,
        role: str = "security",
        status: str = "active",
    ) -> User:
        normalized_username = username.strip().lower()
        if not normalized_username:
            raise ValueError("Username cannot be empty")

        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")

        if self._repository.exists_by_username(normalized_username):
            raise ValueError(f"Username already exists: {normalized_username}")

        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid4()),
            username=normalized_username,
            password_hash=self.hash_password(password),
            role=role.strip().lower(),
            status=status.strip().lower(),
            created_at=now,
            updated_at=now,
        )

        return self._repository.create(user)

    def authenticate(
        self,
        username: str,
        password: str,
    ) -> User:
        normalized_username = username.strip().lower()
        if not normalized_username or not password:
            raise ValueError("Invalid username or password")

        user = self._repository.get_by_username(normalized_username)
        if user is None or not self.verify_password(password, user.password_hash):
            logger.warning(
                "Authentication failed for username=%s",
                normalized_username,
            )
            raise ValueError("Invalid username or password")

        if user.status != "active":
            logger.warning(
                "Authentication rejected for inactive user | username=%s | status=%s",
                normalized_username,
                user.status,
            )
            raise ValueError("User account is inactive")

        logger.info(
            "Authentication successful | user_id=%s | username=%s | role=%s",
            user.id,
            user.username,
            user.role,
        )
        return user

    def create_access_token(
        self,
        user: User,
        expires_delta: timedelta | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        expire = now + (
            expires_delta
            or timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )

        payload: dict[str, Any] = {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.PyJWTError as error:
            logger.warning("JWT decode error: %s", error)
            raise ValueError("Invalid or expired token") from error
