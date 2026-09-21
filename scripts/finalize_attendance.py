import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.logging_config import configure_logging
from app.database.session import SessionFactory
from app.repositories.attendance_repository import AttendanceRepository
from app.services.attendance_service import AttendanceService

IST = ZoneInfo("Asia/Kolkata")
logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    logger.info("======================================")
    logger.info("   Attendance Day Finalization")
    logger.info("======================================")

    session = SessionFactory()

    try:
        repository = AttendanceRepository(session)

        service = AttendanceService(
            repository=repository,
        )

        attendance_date = datetime.now(IST).date()

        logger.info(
            "Finalizing attendance for: %s",
            attendance_date,
        )

        attendances = service.finalize_day(
            attendance_date
        )

        logger.info(
            "Finalized %d attendance record(s)",
            len(attendances),
        )

        for attendance in attendances:
            logger.info(
                "Employee: %s | Check-in: %s | Check-out: %s | Status: %s",
                attendance.employee_id,
                attendance.check_in,
                attendance.check_out,
                attendance.status,
            )

    except Exception as exc:
        logger.error(
            "Attendance finalization failed: %s",
            exc,
        )
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()