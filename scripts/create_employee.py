import argparse
import logging

from app.core.logging_config import configure_logging
from app.database.session import SessionFactory
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.team_repository import TeamRepository
from app.services.employee_registration_service import EmployeeRegistrationService

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register a new employee in the database."
    )
    parser.add_argument(
        "--employee-id",
        required=True,
        help="Unique employee ID (e.g. EMP002)",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Full name of the employee",
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address of the employee",
    )
    parser.add_argument(
        "--department-id",
        default="DEPT001",
        help="Department ID (defaults to DEPT001 - Engineering)",
    )
    parser.add_argument(
        "--team-id",
        default="TEAM001",
        help="Team ID (defaults to TEAM001 - AI Team)",
    )
    parser.add_argument(
        "--designation",
        default="Software Engineer",
        help="Job designation (defaults to Software Engineer)",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    with SessionFactory() as session:
        dept_repo = DepartmentRepository(session)
        team_repo = TeamRepository(session)
        emp_repo = EmployeeRepository(session)

        # Validate department
        dept = dept_repo.get_by_id(args.department_id)
        if dept is None:
            raise ValueError(f"Department '{args.department_id}' does not exist.")

        # Validate team
        team = team_repo.get_by_id(args.team_id)
        if team is None:
            raise ValueError(f"Team '{args.team_id}' does not exist.")

        # Check existing
        existing = emp_repo.get_by_id(args.employee_id)
        if existing is not None:
            print(f"\n[INFO] Employee '{args.employee_id}' already exists in database:")
            print(f"  Name:        {existing.name}")
            print(f"  Email:       {existing.email}")
            print(f"  Department:  {existing.department_id}")
            print(f"  Team:        {existing.team_id}")
            print(f"  Designation: {existing.designation}")
            print(f"  Status:      {existing.status}")
            return

        service = EmployeeRegistrationService(
            employee_repository=emp_repo,
            team_repository=team_repo,
            department_repository=dept_repo,
        )

        employee = service.register(
            employee_id=args.employee_id,
            name=args.name,
            email=args.email,
            department_id=args.department_id,
            team_id=args.team_id,
            designation=args.designation,
        )
        session.commit()

        print("\n======================================")
        print("   EMPLOYEE REGISTERED SUCCESSFULLY   ")
        print("======================================")
        print(f"Employee ID : {employee.employee_id}")
        print(f"Name        : {employee.name}")
        print(f"Email       : {employee.email}")
        print(f"Department  : {employee.department_id} ({dept.department_name})")
        print(f"Team        : {employee.team_id} ({team.team_name})")
        print(f"Designation : {employee.designation}")
        print(f"Status      : {employee.status}")
        print("======================================\n")
        print("Next step: Enroll face vectors using:")
        print(f"  python scripts/register_employee_face.py --employee-id {employee.employee_id}\n")


if __name__ == "__main__":
    main()
