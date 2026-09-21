from dataclasses import dataclass

from app.models.scanner_audit_log import ScannerAuditLog


@dataclass(frozen=True)
class PaginatedAuditLogs:
    items: list[ScannerAuditLog]
    total: int
    page: int
    page_size: int
    total_pages: int
