from datetime import datetime, timezone

from app.models.employee import Employee


def test_employee_creation() -> None:
    now = datetime.now(timezone.utc)

    employee = Employee(
        employee_id="EMP001",
        name="Vigneshwaran",
        email="vigneshwaran@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Software Engineer",
        status="active",
        created_at=now,
        updated_at=now,
    )

    assert employee.employee_id == "EMP001"
    assert employee.name == "Vigneshwaran"
    assert employee.team_id == "TEAM001"
    assert employee.status == "active"