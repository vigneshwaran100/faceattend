import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.database.session import SessionFactory
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.scanner_audit_repository import ScannerAuditRepository
from app.services.attendance_service import AttendanceService
from app.services.scanner_audit_service import ScannerAuditService

logger = logging.getLogger(__name__)


def finalize_attendance_job() -> None:
    """
    Execute daily attendance finalization and automatic absent marking.

    This function creates its own database session because
    it runs independently from the face recognition process.
    """
    session = SessionFactory()

    try:
        attendance_repository = AttendanceRepository(session)
        employee_repository = EmployeeRepository(session)
        audit_repository = ScannerAuditRepository(session)

        service = AttendanceService(
            repository=attendance_repository,
        )
        audit_service = ScannerAuditService(
            repository=audit_repository,
        )

        now = datetime.now(
            AttendanceService.TIMEZONE
        )
        attendance_date = now.date()

        active_employees = employee_repository.get_all_active()
        summary = service.process_end_of_day(
            active_employees=active_employees,
            attendance_date=attendance_date,
            now=now,
        )

        audit_service.log_event(
            scanner_type="SYSTEM",
            event_type="end_of_day_finalization",
            status="SUCCESS",
            message=(
                f"Scheduler EOD completed for {attendance_date} | "
                f"present={summary.present}, "
                f"half_day={summary.half_day}, "
                f"incomplete={summary.incomplete}, "
                f"absent={summary.absent}"
            ),
        )

        logger.info(
            "Daily attendance processing completed for %s | "
            "Present: %d | Half Day: %d | Incomplete: %d | Absent: %d | Total: %d",
            attendance_date,
            summary.present,
            summary.half_day,
            summary.incomplete,
            summary.absent,
            summary.total_processed,
        )

    except Exception as exc:
        logger.error(
            "Attendance finalization failed: %s",
            exc,
        )
        raise

    finally:
        session.close()


def main() -> None:
    configure_logging()

    scheduler = BlockingScheduler(
        timezone="Asia/Kolkata",
    )

    scheduler.add_job(
        finalize_attendance_job,
        trigger="cron",
        hour=settings.end_of_day_hour,
        minute=settings.end_of_day_minute,
        id="daily_attendance_finalization",
        replace_existing=True,
    )

    logger.info("======================================")
    logger.info("   Attendance Scheduler Started")
    logger.info("======================================")
    logger.info(
        "Scheduled finalization & absent marking: Every day at %02d:%02d",
        settings.end_of_day_hour,
        settings.end_of_day_minute,
    )
    logger.info("Timezone: Asia/Kolkata")
    logger.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()

    except KeyboardInterrupt:
        logger.info("Attendance Scheduler stopped.")


if __name__ == "__main__":
    main()