from datetime import datetime, timezone

from app.database.session import SessionFactory
from app.models.department import Department
from app.models.employee import Employee
from app.models.team import Team
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.team_repository import TeamRepository
from app.services.employee_registration_service import (
    EmployeeRegistrationService,
)


def main() -> None:
    with SessionFactory.begin() as session:
        team_repository = TeamRepository(session)
        department_repository = DepartmentRepository(session)
        employee_repository = EmployeeRepository(session)

        now = datetime.now(timezone.utc)

        # Create team if it does not already exist.
        team = team_repository.get_by_id("TEAM001")

        if team is None:
            team = team_repository.create(
                Team(
                    team_id="TEAM001",
                    team_name="AI Team",
                    created_at=now,
                    updated_at=now,
                )
            )

        # Create department if it does not already exist.
        department = department_repository.get_by_id(
            "DEPT001"
        )

        if department is None:
            department = department_repository.create(
                Department(
                    department_id="DEPT001",
                    department_name="Engineering",
                    created_at=now,
                    updated_at=now,
                )
            )

        service = EmployeeRegistrationService(
            employee_repository=employee_repository,
            team_repository=team_repository,
            department_repository=department_repository,
        )

        employee_id = "EMP001"

        # Make the script safe to run repeatedly.
        existing_employee = employee_repository.get_by_id(
            employee_id
        )

        if existing_employee is None:
            employee = service.register(
                employee_id=employee_id,
                name="Vigneshwaran",
                email="vigneshwaran@example.com",
                team_id=team.team_id,
                department_id=department.department_id,
                designation="Software Engineer",
            )

            print("\nEmployee created successfully.")
        else:
            employee = existing_employee

            print("\nEmployee already exists.")

        print("\n========== Employee ==========")
        print(f"Employee ID : {employee.employee_id}")
        print(f"Name        : {employee.name}")
        print(f"Email       : {employee.email}")
        print(f"Team        : {employee.team_id}")
        print(f"Department  : {employee.department_id}")
        print(f"Designation : {employee.designation}")
        print(f"Status      : {employee.status}")
        print(f"Created At  : {employee.created_at}")
        print(f"Updated At  : {employee.updated_at}")
        print("===============================\n")


if __name__ == "__main__":
    main()