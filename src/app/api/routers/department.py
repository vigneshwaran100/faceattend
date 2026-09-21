import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_department_service,
    require_admin,
    require_authenticated,
)
from app.api.schemas.department import (
    DepartmentCreateRequest,
    DepartmentResponse,
)
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.services.department_service import DepartmentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    request: DepartmentCreateRequest,
    service: DepartmentService = Depends(get_department_service),
    current_user: User = Depends(require_admin),
) -> DepartmentResponse:
    try:
        department = service.create_department(
            department_id=request.department_id,
            department_name=request.department_name,
        )

        return DepartmentResponse(
            department_id=department.department_id,
            department_name=department.department_name,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error creating department | error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.get(
    "",
    response_model=list[DepartmentResponse],
)
def list_departments(
    service: DepartmentService = Depends(get_department_service),
    current_user: User = Depends(require_authenticated),
) -> list[DepartmentResponse]:
    try:
        departments = service.list_departments()

        return [
            DepartmentResponse(
                department_id=department.department_id,
                department_name=department.department_name,
                created_at=department.created_at,
                updated_at=department.updated_at,
            )
            for department in departments
        ]

    except DatabaseError as error:
        logger.error(
            "Database error listing departments | error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def get_department(
    department_id: str,
    service: DepartmentService = Depends(get_department_service),
    current_user: User = Depends(require_authenticated),
) -> DepartmentResponse:
    try:
        department = service.get_department(department_id)

        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department not found: {department_id}",
            )

        return DepartmentResponse(
            department_id=department.department_id,
            department_name=department.department_name,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error getting department | department_id=%s | error=%s",
            department_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

