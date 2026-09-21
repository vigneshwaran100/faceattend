import logging

from app.infrastructure.database_error import DatabaseError
from app.models.scanner_processing_result import (
    ScannerProcessingResult,
)
from app.models.scanner_type import ScannerType
from app.repositories.employee_repository import EmployeeRepository
from app.services.attendance_service import AttendanceService
from app.services.recognition_cooldown import RecognitionCooldown
from app.services.recognition_stability_service import (
    RecognitionStabilityService,
)
from app.services.scanner_audit_service import ScannerAuditService

logger = logging.getLogger(__name__)


class ScannerOrchestrationService:
    def __init__(
        self,
        attendance_service: AttendanceService,
        recognition_stability_service: RecognitionStabilityService,
        recognition_cooldown: RecognitionCooldown,
        employee_repository: EmployeeRepository,
        scanner_audit_service: ScannerAuditService | None = None,
    ) -> None:
        self._attendance_service = attendance_service
        self._recognition_stability_service = (
            recognition_stability_service
        )
        self._recognition_cooldown = recognition_cooldown
        self._employee_repository = employee_repository
        self._scanner_audit_service = scanner_audit_service

    def process(
        self,
        employee_id: str | None,
        scanner_type: ScannerType,
    ) -> ScannerProcessingResult:
        logger.debug(
            "Recognition received | employee_id=%s | scanner_type=%s",
            employee_id,
            scanner_type.value,
        )

        confirmation = self._recognition_stability_service.process(
            employee_id
        )

        if confirmation is None:
            return ScannerProcessingResult(
                success=False,
                message="Face not recognized",
            )

        if not confirmation.confirmed:
            logger.debug(
                "Recognition not yet stable | employee_id=%s",
                confirmation.employee_id,
            )
            return ScannerProcessingResult(
                success=False,
                message="Recognition not yet stable",
                employee_id=confirmation.employee_id,
            )

        employee_id = confirmation.employee_id

        employee = self._employee_repository.get_by_id(employee_id)

        if employee is None:
            logger.warning(
                "Recognized employee not found in database | employee_id=%s",
                employee_id,
            )
            if self._scanner_audit_service is not None:
                self._scanner_audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type="employee_not_found",
                    status="FAILURE",
                    employee_id=employee_id,
                    message="Employee not found",
                )
            return ScannerProcessingResult(
                success=False,
                message="Employee not found",
                employee_id=employee_id,
            )

        if employee.status != "active":
            logger.warning(
                "Inactive employee attempted attendance | employee_id=%s",
                employee_id,
            )
            if self._scanner_audit_service is not None:
                self._scanner_audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type="inactive_employee",
                    status="FAILURE",
                    employee_id=employee_id,
                    message="Employee is inactive",
                )
            return ScannerProcessingResult(
                success=False,
                message="Employee is inactive",
                employee_id=employee_id,
            )

        if not self._recognition_cooldown.can_process(
            employee_id
        ):
            logger.debug(
                "Recognition cooldown active | employee_id=%s",
                employee_id,
            )
            if self._scanner_audit_service is not None:
                self._scanner_audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type="cooldown",
                    status="FAILURE",
                    employee_id=employee_id,
                    message="Recognition cooldown active",
                )
            return ScannerProcessingResult(
                success=False,
                message="Recognition cooldown active",
                employee_id=employee_id,
            )

        logger.info(
            "Attendance processing start | employee_id=%s | scanner_type=%s",
            employee_id,
            scanner_type.value,
        )

        try:
            if scanner_type == ScannerType.CHECK_IN:
                self._attendance_service.check_in(employee_id)

            elif scanner_type == ScannerType.CHECK_OUT:
                self._attendance_service.check_out(employee_id)

            else:
                logger.error(
                    "Unsupported scanner type | employee_id=%s | scanner_type=%s",
                    employee_id,
                    scanner_type,
                )
                if self._scanner_audit_service is not None:
                    self._scanner_audit_service.log_event(
                        scanner_type=scanner_type,
                        event_type="unsupported_scanner_type",
                        status="FAILURE",
                        employee_id=employee_id,
                        message="Unsupported scanner type",
                    )
                return ScannerProcessingResult(
                    success=False,
                    message="Unsupported scanner type",
                    employee_id=employee_id,
                )

        except (ValueError, DatabaseError) as error:
            logger.error(
                "Attendance processing failed | employee_id=%s | error=%s",
                employee_id,
                error,
            )
            if self._scanner_audit_service is not None:
                self._scanner_audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type=scanner_type.value,
                    status="FAILURE",
                    employee_id=employee_id,
                    message=str(error),
                )
            return ScannerProcessingResult(
                success=False,
                message=str(error),
                employee_id=employee_id,
            )

        except Exception as error:
            logger.exception(
                "Unexpected attendance processing failure | "
                "employee_id=%s | scanner_type=%s",
                employee_id,
                scanner_type.value,
            )
            if self._scanner_audit_service is not None:
                self._scanner_audit_service.log_event(
                    scanner_type=scanner_type,
                    event_type=scanner_type.value,
                    status="FAILURE",
                    employee_id=employee_id,
                    message=str(error),
                )
            raise

        self._recognition_cooldown.mark_processed(
            employee_id
        )

        logger.info(
            "Attendance success | employee_id=%s | message=%s",
            employee_id,
            f"{scanner_type.value} recorded successfully",
        )

        if self._scanner_audit_service is not None:
            self._scanner_audit_service.log_event(
                scanner_type=scanner_type,
                event_type=scanner_type.value,
                status="SUCCESS",
                employee_id=employee_id,
                message=f"{scanner_type.value} recorded successfully",
            )

        return ScannerProcessingResult(
            success=True,
            message=f"{scanner_type.value} recorded successfully",
            employee_id=employee_id,
        )