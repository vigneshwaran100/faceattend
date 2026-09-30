from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionFactory
from app.infrastructure.milvus_client import MilvusConnection
from app.infrastructure.milvus_v2_repository import MilvusV2Repository
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.scanner_audit_repository import ScannerAuditRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.services.attendance_service import AttendanceService
from app.services.auth_service import AuthService
from app.services.department_service import DepartmentService
from app.services.employee_registration_service import (
    EmployeeRegistrationService,
)
from app.services.face_enrollment_service import FaceEnrollmentService
from app.services.face_quality_service import FaceQualityService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.scanner_audit_service import ScannerAuditService
from app.services.team_service import TeamService
from app.vision.face_engine import FaceEngine
from app.vision.insightface_model import InsightFaceModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_department_repository() -> (
    Generator[DepartmentRepository, None, None]
):
    session: Session = SessionFactory()
    try:
        yield DepartmentRepository(session)
    finally:
        session.close()


def get_department_service() -> (
    Generator[DepartmentService, None, None]
):
    session: Session = SessionFactory()
    try:
        repository = DepartmentRepository(session)
        yield DepartmentService(repository=repository)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_team_repository() -> (
    Generator[TeamRepository, None, None]
):
    session: Session = SessionFactory()
    try:
        yield TeamRepository(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_team_service() -> (
    Generator[TeamService, None, None]
):
    session: Session = SessionFactory()
    try:
        repository = TeamRepository(session)
        yield TeamService(repository=repository)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_employee_repository() -> (
    Generator[EmployeeRepository, None, None]
):
    session: Session = SessionFactory()
    try:
        yield EmployeeRepository(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_employee_registration_service() -> (
    Generator[EmployeeRegistrationService, None, None]
):
    session: Session = SessionFactory()

    try:
        employee_repository = EmployeeRepository(session)
        team_repository = TeamRepository(session)
        department_repository = DepartmentRepository(session)

        service = EmployeeRegistrationService(
            employee_repository=employee_repository,
            team_repository=team_repository,
            department_repository=department_repository,
        )

        yield service
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_attendance_service() -> (
    Generator[AttendanceService, None, None]
):
    session: Session = SessionFactory()

    try:
        attendance_repository = AttendanceRepository(session)
        service = AttendanceService(
            repository=attendance_repository
        )

        yield service
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_scanner_audit_repository() -> (
    Generator[ScannerAuditRepository, None, None]
):
    session: Session = SessionFactory()
    try:
        yield ScannerAuditRepository(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_scanner_audit_service() -> (
    Generator[ScannerAuditService, None, None]
):
    session: Session = SessionFactory()
    try:
        repository = ScannerAuditRepository(session)
        service = ScannerAuditService(repository=repository)
        yield service
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


_face_engine_singleton: FaceEngine | None = None


def get_face_engine() -> FaceEngine:
    global _face_engine_singleton
    if _face_engine_singleton is None:
        model = InsightFaceModel()
        _face_engine_singleton = FaceEngine(model.model)
    return _face_engine_singleton


def get_face_enrollment_service() -> (
    Generator[FaceEnrollmentService, None, None]
):
    milvus_connection = MilvusConnection(
        uri=settings.milvus_uri
    )

    try:
        face_engine = get_face_engine()
        quality_service = FaceQualityService(
            min_confidence=settings.face_quality_min_confidence,
            min_face_size=settings.face_quality_min_face_size,
            min_blur_score=settings.face_quality_min_blur,
        )
        milvus_repository = MilvusV2Repository(
            milvus_connection.client,
            collection_name=settings.milvus_collection_name,
        )

        service = FaceEnrollmentService(
            face_engine=face_engine,
            quality_service=quality_service,
            milvus_repository=milvus_repository,
        )

        yield service

    finally:
        milvus_connection.close()


def get_face_recognition_service() -> (
    Generator[FaceRecognitionService, None, None]
):
    milvus_connection = MilvusConnection(
        uri=settings.milvus_uri
    )

    try:
        milvus_repository = MilvusV2Repository(
            milvus_connection.client,
            collection_name=settings.milvus_collection_name,
        )
        service = FaceRecognitionService(
            repository=milvus_repository,
            threshold=settings.face_similarity_threshold,
        )
        yield service
    finally:
        milvus_connection.close()


def get_user_repository() -> Generator[UserRepository, None, None]:
    session: Session = SessionFactory()
    try:
        yield UserRepository(session)
    finally:
        session.close()


def get_auth_service() -> Generator[AuthService, None, None]:
    session: Session = SessionFactory()
    try:
        repository = UserRepository(session)
        yield AuthService(repository=repository)
    finally:
        session.close()


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = user_repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


class RequireRoles:
    def __init__(self, *allowed_roles: UserRole | str) -> None:
        self.allowed_roles = {
            role.value if isinstance(role, UserRole) else str(role).lower()
            for role in allowed_roles
        }

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_role = (
            current_user.role.value
            if isinstance(current_user.role, UserRole)
            else str(current_user.role).lower()
        )
        if self.allowed_roles and user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user


require_admin = RequireRoles(UserRole.ADMIN)
require_authenticated = RequireRoles(UserRole.ADMIN, UserRole.SECURITY)