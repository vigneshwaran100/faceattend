import logging
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.scanner_audit_log import ScannerAuditLogORM
from app.infrastructure.database_error import DatabaseError
from app.models.scanner_audit_log import ScannerAuditLog
from app.models.scanner_type import ScannerType

logger = logging.getLogger(__name__)


class ScannerAuditRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, audit_log: ScannerAuditLog) -> ScannerAuditLog:
        try:
            scanner_type_val = (
                audit_log.scanner_type.value
                if isinstance(audit_log.scanner_type, ScannerType)
                else str(audit_log.scanner_type)
            )

            record = ScannerAuditLogORM(
                log_id=audit_log.log_id,
                scanner_type=scanner_type_val,
                event_type=audit_log.event_type,
                status=audit_log.status,
                employee_id=audit_log.employee_id,
                similarity=audit_log.similarity,
                message=audit_log.message,
                created_at=audit_log.created_at or datetime.now(),
            )

            self._session.add(record)
            self._session.commit()
            self._session.refresh(record)

            return self._to_domain(record)

        except SQLAlchemyError as error:
            self._session.rollback()
            logger.error(
                "Database error creating scanner audit log | event_type=%s | error=%s",
                audit_log.event_type,
                error,
            )
            raise DatabaseError("Failed to create scanner audit log") from error

    def get_by_id(self, log_id: str) -> ScannerAuditLog | None:
        statement = select(ScannerAuditLogORM).where(
            ScannerAuditLogORM.log_id == log_id
        )
        record = self._session.scalar(statement)
        if record is None:
            return None
        return self._to_domain(record)

    def get_recent(self, limit: int = 100) -> list[ScannerAuditLog]:
        statement = (
            select(ScannerAuditLogORM)
            .order_by(ScannerAuditLogORM.created_at.desc())
            .limit(limit)
        )
        records = self._session.scalars(statement).all()
        return [self._to_domain(record) for record in records]

    def query_logs(
        self,
        employee_id: str | None = None,
        event_type: str | None = None,
        scanner_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ScannerAuditLog], int]:
        try:
            query = select(ScannerAuditLogORM)

            if employee_id:
                query = query.where(
                    ScannerAuditLogORM.employee_id == employee_id.strip()
                )

            if event_type:
                query = query.where(
                    ScannerAuditLogORM.event_type == event_type.strip()
                )

            if scanner_type:
                query = query.where(
                    ScannerAuditLogORM.scanner_type
                    == scanner_type.strip().lower()
                )

            if start_date:
                start_datetime = datetime.combine(start_date, time.min)
                query = query.where(
                    ScannerAuditLogORM.created_at >= start_datetime
                )

            if end_date:
                end_datetime = datetime.combine(end_date, time.max)
                query = query.where(
                    ScannerAuditLogORM.created_at <= end_datetime
                )

            # Count total matching records
            count_statement = select(func.count()).select_from(query.subquery())
            total = self._session.scalar(count_statement) or 0

            # Apply ordering and pagination
            offset = (page - 1) * page_size
            paginated_statement = (
                query.order_by(ScannerAuditLogORM.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            records = self._session.scalars(paginated_statement).all()
            return [self._to_domain(record) for record in records], total

        except SQLAlchemyError as error:
            logger.error("Database error querying audit logs: %s", error)
            raise DatabaseError("Failed to query audit logs") from error

    @staticmethod
    def _to_domain(record: ScannerAuditLogORM) -> ScannerAuditLog:
        return ScannerAuditLog(
            log_id=record.log_id,
            scanner_type=record.scanner_type,
            event_type=record.event_type,
            status=record.status,
            employee_id=record.employee_id,
            similarity=record.similarity,
            message=record.message,
            created_at=record.created_at,
        )
