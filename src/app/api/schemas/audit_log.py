from datetime import datetime
from pydantic import BaseModel


class AuditLogRecordResponse(BaseModel):
    log_id: str
    scanner_type: str
    event_type: str
    status: str
    employee_id: str | None
    similarity: float | None
    message: str | None
    created_at: datetime


class PaginatedAuditLogsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[AuditLogRecordResponse]
