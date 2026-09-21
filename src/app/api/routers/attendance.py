import logging
import numpy as np
from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    get_attendance_service,
    get_employee_repository,
    get_face_engine,
    get_face_recognition_service,
    get_scanner_audit_service,
    require_admin,
    require_authenticated,
)
from app.api.schemas.attendance import (
    DailyAttendanceItemResponse,
    DailyAttendanceReportResponse,
    EndOfDayResponse,
    FaceVerificationResponse,
    KioskStatsResponse,
    ManualPunchRequest,
)
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.repositories.employee_repository import EmployeeRepository
from app.services.attendance_service import AttendanceService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.scanner_audit_service import ScannerAuditService
from app.vision.face_engine import FaceEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attendance", tags=["Attendance"])



@router.get(
    "",
    response_model=DailyAttendanceReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Daily Attendance Report",
)
def get_daily_attendance_report(
    attendance_date: Annotated[
        date | None,
        Query(
            description="Attendance date for the report (defaults to today's date)"
        ),
    ] = None,
    attendance_service: AttendanceService = Depends(get_attendance_service),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    current_user: User = Depends(require_authenticated),
) -> DailyAttendanceReportResponse:
    target_date = (
        attendance_date
        or datetime.now(AttendanceService.TIMEZONE).date()
    )

    try:
        active_employees = employee_repository.get_all_active()
        report = attendance_service.get_daily_attendance_report(
            active_employees=active_employees,
            attendance_date=target_date,
        )

        return DailyAttendanceReportResponse(
            attendance_date=report.attendance_date,
            total_employees=report.total_employees,
            records=[
                DailyAttendanceItemResponse(
                    employee_id=item.employee_id,
                    name=item.name,
                    check_in=item.check_in,
                    check_out=item.check_out,
                    working_hours=item.working_hours,
                    status=item.status,
                )
                for item in report.records
            ],
        )

    except DatabaseError as error:
        logger.error(
            "Database error retrieving daily attendance report | date=%s | error=%s",
            target_date,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily attendance report due to a database error",
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected error retrieving daily attendance report | date=%s | error=%s",
            target_date,
            error,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily attendance report",
        ) from error


@router.post(
    "/end-of-day",
    response_model=EndOfDayResponse,
    status_code=status.HTTP_200_OK,
    summary="Manual End-of-Day Attendance Finalization",
)
def finalize_end_of_day(
    attendance_date: Annotated[
        date | None,
        Query(
            description="Attendance date to finalize (defaults to today's date)"
        ),
    ] = None,
    attendance_service: AttendanceService = Depends(get_attendance_service),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    audit_service: ScannerAuditService = Depends(get_scanner_audit_service),
    current_user: User = Depends(require_admin),
) -> EndOfDayResponse:
    target_date = (
        attendance_date
        or datetime.now(AttendanceService.TIMEZONE).date()
    )

    try:
        active_employees = employee_repository.get_all_active()
        summary = attendance_service.process_end_of_day(
            active_employees=active_employees,
            attendance_date=target_date,
        )

        audit_service.log_event(
            scanner_type="SYSTEM",
            event_type="end_of_day_finalization",
            status="SUCCESS",
            message=(
                f"Manual EOD completed for {target_date} | "
                f"present={summary.present}, "
                f"half_day={summary.half_day}, "
                f"incomplete={summary.incomplete}, "
                f"absent={summary.absent}"
            ),
        )

        return EndOfDayResponse(
            date=summary.attendance_date,
            present=summary.present,
            half_day=summary.half_day,
            incomplete=summary.incomplete,
            absent=summary.absent,
            total_processed=summary.total_processed,
            message="End-of-day attendance finalization completed successfully",
        )

    except DatabaseError as error:
        logger.error(
            "Database error during manual EOD finalization | date=%s | error=%s",
            target_date,
            error,
        )
        audit_service.log_event(
            scanner_type="SYSTEM",
            event_type="end_of_day_finalization",
            status="FAILURE",
            message=f"Database error: {error}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize end-of-day attendance due to a database error",
        ) from error

    except Exception as error:
        logger.exception(
            "Unexpected error during manual EOD finalization | date=%s | error=%s",
            target_date,
            error,
        )
        audit_service.log_event(
            scanner_type="SYSTEM",
            event_type="end_of_day_finalization",
            status="FAILURE",
            message=f"Unexpected error: {error}",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize end-of-day attendance",
        ) from error


@router.post(
    "/verify-face",
    response_model=FaceVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Kiosk: Real-Time Face Verification and Attendance Punch",
)
async def verify_face_and_punch(
    image: UploadFile = File(...),
    scanner_type: Annotated[str, Form()] = "CHECK_IN",
    attendance_service: AttendanceService = Depends(get_attendance_service),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    recognition_service: FaceRecognitionService = Depends(get_face_recognition_service),
    audit_service: ScannerAuditService = Depends(get_scanner_audit_service),
    current_user: User = Depends(require_authenticated),
    face_engine: FaceEngine = Depends(get_face_engine),
) -> FaceVerificationResponse:
    now = datetime.now(AttendanceService.TIMEZONE)
    timestamp = now.isoformat()

    try:
        image_bytes = await image.read()
        if not image_bytes:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="no_face_detected",
                status="FAILURE",
                message="Empty image received",
            )
            return FaceVerificationResponse(
                success=False,
                status="NO_FACE_DETECTED",
                message="Empty image received",
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        nparr = np.frombuffer(image_bytes, np.uint8)
        import cv2
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="no_face_detected",
                status="FAILURE",
                message="Could not decode image",
            )
            return FaceVerificationResponse(
                success=False,
                status="NO_FACE_DETECTED",
                message="Could not decode image",
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        detections, embeddings = face_engine.process(frame)

        # 1. Face Count Validation
        face_count = len(detections) if detections else 0
        if face_count == 0 or not embeddings:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="no_face_detected",
                status="FAILURE",
                message="No face detected in the frame",
            )
            return FaceVerificationResponse(
                success=False,
                status="NO_FACE_DETECTED",
                message="No face detected in the frame",
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        if face_count > 1:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="multiple_faces",
                status="FAILURE",
                message=f"Multiple faces detected in frame (count={face_count})",
            )
            return FaceVerificationResponse(
                success=False,
                status="MULTIPLE_FACES_DETECTED",
                message=f"Multiple faces detected ({face_count}). Please stand one at a time.",
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        # 2. Face Recognition
        embedding_vector = embeddings[0].vector
        result = recognition_service.recognize(embedding_vector)

        if not result.recognized or result.employee_id is None:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="recognition_failed",
                status="FAILURE",
                similarity=result.similarity,
                message=f"Face not recognized (similarity: {result.similarity:.2f})" if result.similarity is not None else "Face not recognized",
            )
            return FaceVerificationResponse(
                success=False,
                status="UNRECOGNIZED_FACE",
                message="Face not recognized. Please ensure your face is clearly visible or use manual punch.",
                similarity=result.similarity,
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        # 4. Employee Existence & Active Status Validation
        employee = employee_repository.get_by_id(result.employee_id)
        if employee is None:
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="employee_not_found",
                status="FAILURE",
                employee_id=result.employee_id,
                similarity=result.similarity,
                message=f"Employee ID {result.employee_id} recognized from biometric index but not found in database",
            )
            return FaceVerificationResponse(
                success=False,
                status="EMPLOYEE_NOT_FOUND",
                message=f"Employee record not found for ID: {result.employee_id}",
                employee_id=result.employee_id,
                similarity=result.similarity,
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        if employee.status != "active":
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="inactive_employee",
                status="FAILURE",
                employee_id=employee.employee_id,
                similarity=result.similarity,
                message=f"Employee {employee.name} ({employee.employee_id}) is inactive (status={employee.status})",
            )
            return FaceVerificationResponse(
                success=False,
                status="INACTIVE_EMPLOYEE",
                message=f"Employee {employee.name} is not active in the system",
                employee_id=employee.employee_id,
                employee_name=employee.name,
                department=employee.department_id,
                job_title=employee.designation,
                similarity=result.similarity,
                scanner_type=scanner_type,
                timestamp=timestamp,
            )

        # 5. Attendance Transaction & Checkout Error Handling
        if scanner_type == "CHECK_IN":
            attendance = attendance_service.check_in(employee.employee_id)
            audit_service.log_event(
                scanner_type=scanner_type,
                event_type="face_scan",
                status="SUCCESS",
                employee_id=employee.employee_id,
                similarity=result.similarity,
                message=f"CHECK_IN recorded via kiosk for {employee.name}",
            )
            return FaceVerificationResponse(
                success=True,
                status="ACCESS_GRANTED",
                message=f"Check-In recorded for {employee.name}",
                employee_id=employee.employee_id,
                employee_name=employee.name,
                department=employee.department_id,
                job_title=employee.designation,
                similarity=result.similarity,
                scanner_type=scanner_type,
                timestamp=timestamp,
                attendance_id=attendance.attendance_id,
            )
        elif scanner_type == "CHECK_OUT":
            try:
                attendance = attendance_service.check_out(employee.employee_id)
                audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type="face_scan",
                    status="SUCCESS",
                    employee_id=employee.employee_id,
                    similarity=result.similarity,
                    message=f"CHECK_OUT recorded via kiosk for {employee.name}",
                )
                return FaceVerificationResponse(
                    success=True,
                    status="ACCESS_GRANTED",
                    message=f"Check-Out recorded for {employee.name}",
                    employee_id=employee.employee_id,
                    employee_name=employee.name,
                    department=employee.department_id,
                    job_title=employee.designation,
                    similarity=result.similarity,
                    scanner_type=scanner_type,
                    timestamp=timestamp,
                    attendance_id=attendance.attendance_id,
                )
            except ValueError as error:
                audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type="no_check_in",
                    status="FAILURE",
                    employee_id=employee.employee_id,
                    similarity=result.similarity,
                    message=f"Check-out rejected for {employee.name}: {error}",
                )
                return FaceVerificationResponse(
                    success=False,
                    status="NO_CHECK_IN",
                    message=f"No check-in record found for {employee.name} today. Please check in first.",
                    employee_id=employee.employee_id,
                    employee_name=employee.name,
                    department=employee.department_id,
                    job_title=employee.designation,
                    similarity=result.similarity,
                    scanner_type=scanner_type,
                    timestamp=timestamp,
                    attendance_id=None,
                )
        else:
            return FaceVerificationResponse(
                success=False,
                status="ERROR",
                message=f"Invalid scanner_type: {scanner_type}",
                timestamp=timestamp,
            )

    except HTTPException:
        raise
    except Exception as error:
        logger.exception(
            "Unexpected error in kiosk face verification | error=%s", error
        )
        return FaceVerificationResponse(
            success=False,
            status="ERROR",
            message="Internal server error during face verification",
            timestamp=timestamp,
        )
    finally:
        await image.close()


@router.post(
    "/manual-punch",
    response_model=FaceVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Kiosk: Manual Attendance Punch by Employee ID",
)
def manual_punch(
    request: ManualPunchRequest,
    attendance_service: AttendanceService = Depends(get_attendance_service),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    audit_service: ScannerAuditService = Depends(get_scanner_audit_service),
    current_user: User = Depends(require_authenticated),
) -> FaceVerificationResponse:
    now = datetime.now(AttendanceService.TIMEZONE)
    timestamp = now.isoformat()

    employee = employee_repository.get_by_id(request.employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {request.employee_id}",
        )

    if employee.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee {employee.name} is not active",
        )

    attendance_id = None
    if request.scanner_type == "CHECK_IN":
        attendance = attendance_service.check_in(employee.employee_id)
        attendance_id = attendance.attendance_id
    elif request.scanner_type == "CHECK_OUT":
        try:
            attendance = attendance_service.check_out(employee.employee_id)
            attendance_id = attendance.attendance_id
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scanner_type must be CHECK_IN or CHECK_OUT",
        )

    audit_service.log_event(
        scanner_type=request.scanner_type,
        event_type="manual_punch",
        status="SUCCESS",
        employee_id=employee.employee_id,
        message=f"Manual {request.scanner_type} by operator {current_user.username}",
    )

    return FaceVerificationResponse(
        success=True,
        status="ACCESS_GRANTED",
        message=f"Manual {request.scanner_type.replace('_', '-')} recorded for {employee.name}",
        employee_id=employee.employee_id,
        employee_name=employee.name,
        department=employee.department_id,
        job_title=employee.designation,
        scanner_type=request.scanner_type,
        timestamp=timestamp,
        attendance_id=attendance_id,
    )


@router.get(
    "/kiosk-stats",
    response_model=KioskStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Kiosk: Today's Gate Statistics",
)
def get_kiosk_stats(
    attendance_service: AttendanceService = Depends(get_attendance_service),
    employee_repository: EmployeeRepository = Depends(get_employee_repository),
    audit_service: ScannerAuditService = Depends(get_scanner_audit_service),
    current_user: User = Depends(require_authenticated),
) -> KioskStatsResponse:
    from datetime import date as date_type
    today = datetime.now(AttendanceService.TIMEZONE).date()

    active_employees = employee_repository.get_all_active()
    report = attendance_service.get_daily_attendance_report(
        active_employees=active_employees,
        attendance_date=today,
    )

    checked_in = sum(
        1 for r in report.records
        if r.check_in is not None and r.status in ("in_progress", "present", "half_day")
    )
    checked_out = sum(
        1 for r in report.records
        if r.check_out is not None
    )

    # Audit logs for today's scan counts
    audit_result = audit_service.get_logs(
        start_date=today,
        end_date=today,
        page=1,
        page_size=1,
    )
    total_scans = audit_result.total

    success_audit = audit_service.get_logs(
        start_date=today,
        end_date=today,
        event_type="face_scan",
        page=1,
        page_size=1,
    )
    successful = success_audit.total

    return KioskStatsResponse(
        date=today,
        total_scans_today=total_scans,
        successful_punches=successful,
        rejected_scans=max(0, total_scans - successful),
        active_employees=report.total_employees,
        checked_in_count=checked_in,
        checked_out_count=checked_out,
    )
