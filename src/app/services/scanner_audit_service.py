import logging
from datetime import date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.models.paginated_audit_logs import PaginatedAuditLogs
from app.models.scanner_audit_log import ScannerAuditLog
from app.models.scanner_type import ScannerType
from app.repositories.scanner_audit_repository import ScannerAuditRepository

logger = logging.getLogger(__name__)


class ScannerAuditService:
    TIMEZONE = ZoneInfo("Asia/Kolkata")

    def __init__(self, repository: ScannerAuditRepository) -> None:
        self._repository = repository

    def log_event(
        self,
        scanner_type: ScannerType | str,
        event_type: str,
        status: str,
        *,
        employee_id: str | None = None,
        similarity: float | None = None,
        message: str | None = None,
        now: datetime | None = None,
    ) -> ScannerAuditLog | None:
        try:
            current_time = now or datetime.now(self.TIMEZONE)
            scanner_type_val = (
                scanner_type.value
                if isinstance(scanner_type, ScannerType)
                else str(scanner_type)
            )

            audit_log = ScannerAuditLog(
                log_id=str(uuid4()),
                scanner_type=scanner_type_val,
                event_type=event_type,
                status=status,
                employee_id=employee_id,
                similarity=similarity,
                message=message,
                created_at=current_time,
            )

            return self._repository.create(audit_log)

        except Exception as error:
            logger.error(
                "Failed to record scanner audit log | scanner_type=%s | "
                "event_type=%s | status=%s | employee_id=%s | error=%s",
                scanner_type,
                event_type,
                status,
                employee_id,
                error,
            )
            return None

    def get_logs(
        self,
        employee_id: str | None = None,
        event_type: str | None = None,
        scanner_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedAuditLogs:
        items, total = self._repository.query_logs(
            employee_id=employee_id,
            event_type=event_type,
            scanner_type=scanner_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        total_pages = (
            (total + page_size - 1) // page_size if total > 0 else 0
        )

        return PaginatedAuditLogs(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
