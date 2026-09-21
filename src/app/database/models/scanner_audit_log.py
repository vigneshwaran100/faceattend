from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ScannerAuditLogORM(Base):
    __tablename__ = "scanner_audit_logs"

    log_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    scanner_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    employee_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("employees.employee_id"),
        nullable=True,
    )

    similarity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_scanner_audit_logs_event_type", "event_type"),
        Index("ix_scanner_audit_logs_status", "status"),
        Index("ix_scanner_audit_logs_employee_id", "employee_id"),
        Index("ix_scanner_audit_logs_created_at", "created_at"),
    )
