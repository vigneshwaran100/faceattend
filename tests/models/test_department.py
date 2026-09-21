from datetime import datetime, timezone

from app.models.department import Department


def test_department_creation() -> None:
    now = datetime.now(timezone.utc)

    department = Department(
        department_id="DEPT001",
        department_name="Engineering",
        created_at=now,
        updated_at=now,
    )

    assert department.department_id == "DEPT001"
    assert department.department_name == "Engineering"