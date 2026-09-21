from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.dependencies import (
    RequireRoles,
    get_current_user,
    get_department_service,
    get_employee_registration_service,
    get_employee_repository,
    get_team_service,
)
from app.api.main import app
from app.models.department import Department
from app.models.employee import Employee
from app.models.team import Team
from app.models.user import User
from app.models.user_role import UserRole


@pytest.fixture
def admin_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id="ADMIN001",
        username="admin_user",
        password_hash="hash",
        role="admin",
        status="active",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def security_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id="SEC001",
        username="security_user",
        password_hash="hash",
        role="security",
        status="active",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def client() -> TestClient:
    yield TestClient(app)
    app.dependency_overrides.clear()



def test_require_roles_unit_logic(admin_user: User, security_user: User) -> None:
    admin_only_checker = RequireRoles(UserRole.ADMIN)
    assert admin_only_checker(admin_user) == admin_user

    with pytest.raises(HTTPException) as exc_info:
        admin_only_checker(security_user)
    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()

    multi_role_checker = RequireRoles(UserRole.ADMIN, UserRole.SECURITY)
    assert multi_role_checker(admin_user) == admin_user
    assert multi_role_checker(security_user) == security_user


def test_unauthenticated_request_rejected(client: TestClient) -> None:
    endpoints = [
        ("GET", "/departments", None),
        ("POST", "/departments", {"department_id": "D1", "department_name": "Dept"}),
        ("GET", "/departments/D1", None),
        ("GET", "/teams", None),
        ("POST", "/teams", {"team_id": "T1", "team_name": "Team"}),
        ("GET", "/teams/T1", None),
        ("GET", "/employees", None),
        ("POST", "/employees", {"employee_id": "E1", "name": "Emp", "email": "e@x.com", "team_id": "T1", "department_id": "D1", "designation": "Eng"}),
        ("GET", "/employees/E1", None),
        ("PATCH", "/employees/E1/status", {"status": "inactive"}),
        ("GET", "/employees/E1/attendance", None),
        ("GET", "/employees/E1/attendance/summary", None),
        ("GET", "/attendance", None),
        ("POST", "/attendance/end-of-day", None),
        ("GET", "/audit-logs", None),
    ]

    for method, url, payload in endpoints:
        if method == "GET":
            response = client.get(url)
        elif method == "POST":
            response = client.post(url, json=payload)
        elif method == "PATCH":
            response = client.patch(url, json=payload)

        assert response.status_code == 401, f"Failed on {method} {url}: {response.status_code}"


def test_security_role_forbidden_on_admin_only_endpoints(
    client: TestClient,
    security_user: User,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: security_user

    admin_endpoints = [
        ("POST", "/departments", {"department_id": "D1", "department_name": "Dept"}),
        ("POST", "/teams", {"team_id": "T1", "team_name": "Team"}),
        ("POST", "/employees", {"employee_id": "E1", "name": "Emp", "email": "e@x.com", "team_id": "T1", "department_id": "D1", "designation": "Eng"}),
        ("PATCH", "/employees/E1/status", {"status": "inactive"}),
        ("POST", "/attendance/end-of-day", None),
        ("GET", "/audit-logs", None),
    ]

    for method, url, payload in admin_endpoints:
        if method == "GET":
            response = client.get(url)
        elif method == "POST":
            response = client.post(url, json=payload)
        elif method == "PATCH":
            response = client.patch(url, json=payload)

        assert response.status_code == 403, f"Expected 403 on {method} {url}, got {response.status_code}"
        assert "permission" in response.json()["detail"].lower()


def test_security_role_allowed_on_view_endpoints(
    client: TestClient,
    security_user: User,
) -> None:
    from app.api.dependencies import get_attendance_service
    from app.models.attendance_summary import AttendanceSummary

    app.dependency_overrides[get_current_user] = lambda: security_user

    dept_service = Mock()
    now = datetime.now(timezone.utc)
    dept_service.list_departments.return_value = []
    dept_service.get_department.return_value = Department(
        department_id="DEPT001",
        department_name="Engineering",
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_department_service] = lambda: dept_service

    team_service = Mock()
    team_service.list_teams.return_value = []
    team_service.get_team.return_value = Team(
        team_id="TEAM001",
        team_name="AI Team",
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_team_service] = lambda: team_service

    emp_repo = Mock()
    emp_repo.get_all_active.return_value = []
    emp_repo.get_by_id.return_value = Employee(
        employee_id="EMP001",
        name="Vignesh",
        email="v@example.com",
        team_id="TEAM001",
        department_id="DEPT001",
        designation="Engineer",
        status="active",
        created_at=now,
        updated_at=now,
    )
    app.dependency_overrides[get_employee_repository] = lambda: emp_repo

    att_service = Mock()
    att_service.get_attendance_history_by_date_range.return_value = []
    att_service.get_attendance_summary.return_value = AttendanceSummary(
        employee_id="EMP001",
        start_date=None,
        end_date=None,
        total_records=0,
        total_working_days=0,
        present_days=0,
        half_days=0,
        incomplete_days=0,
        absent_days=0,
        in_progress_days=0,
        total_working_hours=0.0,
        attendance_percentage=0.0,
    )
    app.dependency_overrides[get_attendance_service] = lambda: att_service

    res_depts = client.get("/departments")
    assert res_depts.status_code == 200

    res_dept = client.get("/departments/DEPT001")
    assert res_dept.status_code == 200

    res_teams = client.get("/teams")
    assert res_teams.status_code == 200

    res_team = client.get("/teams/TEAM001")
    assert res_team.status_code == 200

    res_emps = client.get("/employees")
    assert res_emps.status_code == 200

    res_emp = client.get("/employees/EMP001")
    assert res_emp.status_code == 200

    res_att_hist = client.get("/employees/EMP001/attendance")
    assert res_att_hist.status_code == 200

    res_att_sum = client.get("/employees/EMP001/attendance/summary")
    assert res_att_sum.status_code == 200




def test_public_endpoints_accessible_without_auth(client: TestClient) -> None:
    res_health = client.get("/health")
    assert res_health.status_code == 200

    res_login = client.post("/auth/login", json={"username": "", "password": ""})
    assert res_login.status_code in (400, 401, 422)
