import logging
from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from app.api.dependencies import (
    get_attendance_service,
    get_employee_registration_service,
    get_employee_repository,
    get_face_enrollment_service,
    require_admin,
    require_authenticated,
)
from app.api.schemas.attendance import (
    AttendanceHistoryResponse,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
)
from app.api.schemas.employee import (
    EmployeeCreateRequest,
    EmployeeResponse,
    EmployeeStatusUpdateRequest,
    EmployeeUpdateRequest,
    FaceEnrollmentResponse,
    FaceSamplesEnrollmentResponse,
)
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.repositories.employee_repository import EmployeeRepository
from app.services.attendance_service import AttendanceService
from app.services.employee_registration_service import (
    EmployeeRegistrationService,
)
from app.services.face_enrollment_service import (
    FaceEnrollmentService,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


def _validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> None:
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    request: EmployeeCreateRequest,
    service: EmployeeRegistrationService = Depends(
        get_employee_registration_service
    ),
    current_user: User = Depends(require_admin),
) -> EmployeeResponse:
    try:
        employee = service.register(
            employee_id=request.employee_id,
            name=request.name,
            email=str(request.email),
            team_id=request.team_id,
            department_id=request.department_id,
            designation=request.designation,
        )

        return EmployeeResponse(
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

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "",
    response_model=list[EmployeeResponse],
)
def list_employees(
    repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    current_user: User = Depends(require_authenticated),
) -> list[EmployeeResponse]:
    try:
        employees = repository.get_all_active()

        return [
            EmployeeResponse(
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
            for employee in employees
        ]

    except DatabaseError as error:
        logger.error(
            "Database error listing employees | error=%s",
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def get_employee(
    employee_id: str,
    repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    current_user: User = Depends(require_authenticated),
) -> EmployeeResponse:
    employee = repository.get_by_id(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}",
        )

    return EmployeeResponse(
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


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
)
def update_employee(
    employee_id: str,
    request: EmployeeUpdateRequest,
    service: EmployeeRegistrationService = Depends(
        get_employee_registration_service
    ),
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    current_user: User = Depends(require_admin),
) -> EmployeeResponse:
    if not employee_repository.exists(employee_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}",
        )

    try:
        updated = service.update(
            employee_id=employee_id,
            name=request.name,
            email=str(request.email),
            team_id=request.team_id,
            department_id=request.department_id,
            designation=request.designation,
            status=request.status,
        )

        return EmployeeResponse(
            employee_id=updated.employee_id,
            name=updated.name,
            email=updated.email,
            team_id=updated.team_id,
            department_id=updated.department_id,
            designation=updated.designation,
            status=updated.status,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error updating employee | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.patch(
    "/{employee_id}/status",
    response_model=EmployeeResponse,
)
def update_employee_status(
    employee_id: str,
    request: EmployeeStatusUpdateRequest,
    service: EmployeeRegistrationService = Depends(
        get_employee_registration_service
    ),
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    current_user: User = Depends(require_admin),
) -> EmployeeResponse:
    if not employee_repository.exists(employee_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}",
        )

    try:
        updated = service.set_status(
            employee_id=employee_id,
            status=request.status,
        )

        return EmployeeResponse(
            employee_id=updated.employee_id,
            name=updated.name,
            email=updated.email,
            team_id=updated.team_id,
            department_id=updated.department_id,
            designation=updated.designation,
            status=updated.status,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except DatabaseError as error:
        logger.error(
            "Database error updating employee status | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error


@router.post(
    "/{employee_id}/face",
    response_model=FaceEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_employee_face(
    employee_id: str,
    image: UploadFile = File(...),
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    enrollment_service: FaceEnrollmentService = Depends(
        get_face_enrollment_service
    ),
    current_user: User = Depends(require_authenticated),
) -> FaceEnrollmentResponse:
    employee = employee_repository.get_by_id(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}",
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee is not active: {employee_id}",
        )

    if image.content_type and not (
        image.content_type.startswith("image/")
        or image.content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image (JPEG, PNG, etc.)",
        )

    try:
        image_bytes = await image.read()

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image is empty",
            )

        enrollment_service.enroll_image(
            employee=employee,
            image_bytes=image_bytes,
        )

        return FaceEnrollmentResponse(
            employee_id=employee.employee_id,
            message="Face enrolled successfully",
        )

    except HTTPException:
        raise

    except ValueError as error:
        logger.warning(
            "Face single enrollment rejected | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.error(
            "Unexpected error enrolling face | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

    finally:
        await image.close()


@router.post(
    "/{employee_id}/face/samples",
    response_model=FaceSamplesEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_employee_face_samples(
    employee_id: str,
    images: list[UploadFile] = File(...),
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    enrollment_service: FaceEnrollmentService = Depends(
        get_face_enrollment_service
    ),
    current_user: User = Depends(require_authenticated),
) -> FaceSamplesEnrollmentResponse:
    employee = employee_repository.get_by_id(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {employee_id}",
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee is not active: {employee_id}",
        )

    if len(images) != FaceEnrollmentService.TARGET_SAMPLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Exactly {FaceEnrollmentService.TARGET_SAMPLES} face sample "
                f"images are required, received {len(images)}"
            ),
        )

    image_bytes_list: list[bytes] = []
    try:
        for index, img in enumerate(images, start=1):
            if img.content_type and not (
                img.content_type.startswith("image/")
                or img.content_type == "application/octet-stream"
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sample {index}: Uploaded file must be an image (JPEG, PNG, etc.)",
                )

            data = await img.read()
            if not data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sample {index}: Uploaded image is empty",
                )
            image_bytes_list.append(data)

        stored_count = enrollment_service.enroll_samples(
            employee=employee,
            image_bytes_list=image_bytes_list,
        )

        return FaceSamplesEnrollmentResponse(
            employee_id=employee.employee_id,
            samples_received=len(image_bytes_list),
            embeddings_stored=stored_count,
            enrollment_status="success",
            message=f"Successfully enrolled {stored_count} face samples for employee {employee.employee_id}",
        )

    except HTTPException:
        raise

    except ValueError as error:
        logger.warning(
            "Face samples enrollment rejected | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.error(
            "Unexpected error enrolling face samples | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

    finally:
        for img in images:
            await img.close()


@router.get(
    "/{employee_id}/attendance",
    response_model=AttendanceHistoryResponse,
)

def get_employee_attendance(
    employee_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    attendance_service: AttendanceService = Depends(
        get_attendance_service
    ),
    current_user: User = Depends(require_authenticated),
) -> AttendanceHistoryResponse:
    _validate_date_range(start_date, end_date)

    try:
        employee = employee_repository.get_by_id(employee_id)

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee not found: {employee_id}",
            )

        attendance_records = (
            attendance_service.get_attendance_history_by_date_range(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

        return AttendanceHistoryResponse(
            employee_id=employee_id,
            attendance=[
                AttendanceRecordResponse(
                    attendance_id=record.attendance_id,
                    employee_id=record.employee_id,
                    attendance_date=record.attendance_date,
                    check_in=record.check_in,
                    check_out=record.check_out,
                    status=record.status,
                    working_hours=(
                        AttendanceService.calculate_working_hours(
                            record.check_in,
                            record.check_out,
                        )
                        if record.check_in is not None
                        and record.check_out is not None
                        else None
                    ),
                )
                for record in attendance_records
            ],
        )

    except HTTPException:
        raise

    except DatabaseError as error:
        logger.error(
            "Database error retrieving attendance history | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.get(
    "/{employee_id}/attendance/summary",
    response_model=AttendanceSummaryResponse,
)
def get_employee_attendance_summary(
    employee_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_repository: EmployeeRepository = Depends(
        get_employee_repository
    ),
    attendance_service: AttendanceService = Depends(
        get_attendance_service
    ),
    current_user: User = Depends(require_authenticated),
) -> AttendanceSummaryResponse:
    _validate_date_range(start_date, end_date)

    try:
        employee = employee_repository.get_by_id(employee_id)

        if employee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee not found: {employee_id}",
            )

        summary = attendance_service.get_attendance_summary(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )

        return AttendanceSummaryResponse(
            employee_id=summary.employee_id,
            start_date=summary.start_date,
            end_date=summary.end_date,
            total_records=summary.total_records,
            total_working_days=summary.total_working_days,
            present_days=summary.present_days,
            half_days=summary.half_days,
            incomplete_days=summary.incomplete_days,
            absent_days=summary.absent_days,
            in_progress_days=summary.in_progress_days,
            total_working_hours=summary.total_working_hours,
            attendance_percentage=summary.attendance_percentage,
        )

    except HTTPException:
        raise

    except DatabaseError as error:
        logger.error(
            "Database error retrieving attendance summary | employee_id=%s | error=%s",
            employee_id,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error