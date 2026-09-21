from dataclasses import dataclass
from datetime import datetime

from app.models.scanner_type import ScannerType


@dataclass(frozen=True)
class ScannerAuditLog:
    log_id: str
    scanner_type: ScannerType | str
    event_type: str
    status: str
    employee_id: str | None = None
    similarity: float | None = None
    message: str | None = None
    created_at: datetime | None = None
