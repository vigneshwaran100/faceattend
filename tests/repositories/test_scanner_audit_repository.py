from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.scanner_audit_log import ScannerAuditLog
from app.repositories.scanner_audit_repository import ScannerAuditRepository
from app.services.scanner_audit_service import ScannerAuditService


def create_test_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_and_get_by_id() -> None:
    session = create_test_session()
    repository = ScannerAuditRepository(session)

    log_entry = ScannerAuditLog(
        log_id="LOG001",
        scanner_type="check_in",
        event_type="attendance_success",
        status="SUCCESS",
        employee_id="EMP001",
        similarity=0.85,
        message="Check-in successful",
        created_at=datetime.now(timezone.utc),
    )

    created = repository.create(log_entry)
    assert created.log_id == "LOG001"

    retrieved = repository.get_by_id("LOG001")
    assert retrieved is not None
    assert retrieved.employee_id == "EMP001"
    assert retrieved.status == "SUCCESS"


def test_query_logs_with_pagination_and_filters() -> None:
    session = create_test_session()
    repository = ScannerAuditRepository(session)
    service = ScannerAuditService(repository)

    base_time = datetime(2026, 8, 29, 10, 0, 0)

    for i in range(1, 6):
        repository.create(
            ScannerAuditLog(
                log_id=f"LOG00{i}",
                scanner_type="check_in" if i % 2 == 1 else "check_out",
                event_type="success" if i <= 3 else "failure",
                status="SUCCESS" if i <= 3 else "FAILURE",
                employee_id="EMP001" if i <= 4 else "EMP002",
                similarity=0.80,
                message=f"Log message {i}",
                created_at=datetime(2026, 8, 29, 10, i, 0),
            )
        )

    # Test query all with page_size=2
    paginated = service.get_logs(page=1, page_size=2)
    assert paginated.total == 5
    assert paginated.total_pages == 3
    assert len(paginated.items) == 2
    assert paginated.page == 1
    assert paginated.page_size == 2

    # Test filtering by employee_id
    paginated_emp = service.get_logs(employee_id="EMP001")
    assert paginated_emp.total == 4

    # Test filtering by event_type
    paginated_evt = service.get_logs(event_type="failure")
    assert paginated_evt.total == 2

    # Test filtering by date range
    paginated_date = service.get_logs(
        start_date=date(2026, 8, 29),
        end_date=date(2026, 8, 29),
    )
    assert paginated_date.total == 5
