import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_scanner_audit_service,
    require_admin,
)
from app.api.schemas.audit_log import (
    AuditLogRecordResponse,
    PaginatedAuditLogsResponse,
)
from app.infrastructure.database_error import DatabaseError
from app.models.user import User
from app.services.scanner_audit_service import ScannerAuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def _validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )


@router.get(
    "",
    response_model=PaginatedAuditLogsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Audit Logs",
)
def get_audit_logs(
    employee_id: Annotated[
        str | None,
        Query(description="Filter by employee ID"),
    ] = None,
    event_type: Annotated[
        str | None,
        Query(description="Filter by event type"),
    ] = None,
    scanner_type: Annotated[
        str | None,
        Query(description="Filter by scanner type"),
    ] = None,
    start_date: Annotated[
        date | None,
        Query(description="Filter logs from start date"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Filter logs up to end date"),
    ] = None,
    page: Annotated[
        int,
        Query(ge=1, description="Page number (1-indexed)"),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100, description="Number of items per page"),
    ] = 20,
    service: ScannerAuditService = Depends(get_scanner_audit_service),
    current_user: User = Depends(require_admin),
) -> PaginatedAuditLogsResponse:
    _validate_date_range(start_date, end_date)

    try:
        paginated_result = service.get_logs(
            employee_id=employee_id,
            event_type=event_type,
            scanner_type=scanner_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
        )

        return PaginatedAuditLogsResponse(
            total=paginated_result.total,
            page=paginated_result.page,
            page_size=paginated_result.page_size,
            total_pages=paginated_result.total_pages,
            items=[
                AuditLogRecordResponse(
                    log_id=item.log_id,
                    scanner_type=item.scanner_type,
                    event_type=item.event_type,
                    status=item.status,
                    employee_id=item.employee_id,
                    similarity=item.similarity,
                    message=item.message,
                    created_at=item.created_at,
                )
                for item in paginated_result.items
            ],
        )

    except HTTPException:
        raise

    except DatabaseError as error:
        logger.error("Database error retrieving audit logs: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs due to a database error",
        ) from error

    except Exception as error:
        logger.exception("Unexpected error retrieving audit logs: %s", error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        ) from error
